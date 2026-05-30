"""
Knowledge Base Ingest Pipeline
Reads all .md files from docs/, chunks them, embeds with sentence-transformers,
and stores in a persistent ChromaDB collection.

Run: python knowledge_base/ingest.py
     python knowledge_base/ingest.py --reset  (clears existing collection first)
"""
import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force load .env from the backend directory
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Chunk settings (matching PRD specification)
CHUNK_SIZE_TOKENS = 300
OVERLAP_TOKENS = 50
WORDS_PER_TOKEN = 0.75  # Approximate: 1 token ≈ 0.75 words
CHUNK_SIZE_WORDS = int(CHUNK_SIZE_TOKENS * WORDS_PER_TOKEN)  # ≈ 225 words
OVERLAP_WORDS = int(OVERLAP_TOKENS * WORDS_PER_TOKEN)         # ≈ 38 words

COLLECTION_NAME = "astrology_knowledge"
DOCS_PATH = Path(__file__).parent / "docs"
CHROMA_PATH = Path(__file__).parent / "chroma_store"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def ingest(reset: bool = False) -> None:
    import chromadb
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    print("Initializing ChromaDB and embedding model...")
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    print("  Embedding model loaded: models/gemini-embedding-001")

    # Scan all .md files
    md_files = list(DOCS_PATH.rglob("*.md"))
    print(f"  Found {len(md_files)} markdown documents in docs/")

    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_metadatas: list[dict] = []

    for filepath in sorted(md_files):
        relative = filepath.relative_to(DOCS_PATH)
        category = str(relative.parts[0]) if len(relative.parts) > 1 else "general"
        source = str(relative).replace("\\", "/")

        text = filepath.read_text(encoding="utf-8").strip()
        if not text:
            continue

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{source}::chunk_{i}"
            all_ids.append(chunk_id)
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": source,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "filename": filepath.name,
            })

    print(f"  Total chunks to embed: {len(all_chunks)}")

    import time
    embeddings: list[list[float]] = []
    for idx, chunk in enumerate(all_chunks):
        for attempt in range(5):
            try:
                emb = model.embed_query(chunk)
                embeddings.append(emb)
                # Sleep 0.6 seconds to stay well below the 100 RPM free tier limit
                time.sleep(0.6)
                break
            except Exception as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    sleep_time = 2 ** attempt + 5
                    print(f"  [Rate Limit] Exceeded embedding quota on chunk {idx + 1}/{len(all_chunks)}. Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    raise e
        if len(embeddings) != idx + 1:
            raise RuntimeError(f"Failed to generate embedding for chunk {idx}")
        if (idx + 1) % 10 == 0 or idx + 1 == len(all_chunks):
            print(f"  Embedded {idx + 1}/{len(all_chunks)} chunks...")

    collection.upsert(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )
    print(f"\n[SUCCESS] Ingest complete. {len(all_chunks)} chunks stored in ChromaDB.")
    print(f"  Collection: '{COLLECTION_NAME}' at {CHROMA_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest astrology docs into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Delete and rebuild the collection")
    args = parser.parse_args()
    ingest(reset=args.reset)