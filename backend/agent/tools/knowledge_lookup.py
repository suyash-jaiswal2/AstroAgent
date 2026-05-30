"""
Tool 4: knowledge_lookup
Semantic search over the curated astrology knowledge base using ChromaDB.
Retrieves the top 3 most relevant document chunks for a given query.
"""
import json
import os
from functools import lru_cache

from langchain_core.tools import tool

CHROMA_PATH = os.getenv("CHROMA_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base", "chroma_store")))
COLLECTION_NAME = "astrology_knowledge"


@lru_cache(maxsize=1)
def _get_collection():
    """Lazily initialize ChromaDB collection (cached after first call)."""
    import chromadb
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        # Collection not yet created — ingest.py must be run first
        return None, None

    model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    return collection, model


@tool
def knowledge_lookup(query: str, context: str = "") -> str:
    """
    Search the curated astrology knowledge base for information relevant to a query.
    Use this tool to retrieve accurate interpretations of planets, signs, houses,
    aspects, transits, yogas, nakshatras, muhurta rules, and compatibility guidelines.
    Always call this after computing chart data to ground your interpretation.

    Args:
        query: Natural language query, e.g. 'Jupiter in Sagittarius career meaning'
               or 'Gaja Kesari yoga interpretation' or 'Saturn transit 10th house'
        context: Optional additional context to refine the search, e.g. 'Vedic astrology'
    """
    collection, model = _get_collection()

    if collection is None:
        return json.dumps({
            "error": "Knowledge base not initialized. Run: python knowledge_base/ingest.py",
            "query": query,
        })

    try:
        full_query = f"{context} {query}".strip() if context else query
        embedding = model.embed_query(full_query)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        formatted = {
            "query": query,
            "results": [
                {
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "category": meta.get("category", "general"),
                    "relevance_score": round(1 - float(dist), 4),
                }
                for doc, meta, dist in zip(docs, metas, dists)
            ],
        }
        return json.dumps(formatted)

    except Exception as e:
        return json.dumps({"error": f"Knowledge lookup failed: {str(e)}", "query": query})