import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .routes import chat, sessions, chart, eval_routes
from db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    await init_db()
    
    # Dynamic ChromaDB Ingestion
    chroma_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "chroma_store"))
    if not os.path.exists(chroma_path) or not os.listdir(chroma_path):
        print("ChromaDB store is missing or empty. Running dynamic knowledge base ingestion...")
        try:
            from knowledge_base.ingest import ingest
            ingest(reset=True)
            print("ChromaDB knowledge base successfully ingested.")
        except Exception as e:
            print(f"ChromaDB dynamic ingestion failed: {e}")
            
    yield
    # ── Shutdown ───────────────────────────────────────────────────────────────


app = FastAPI(title="AstroAgent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://astro-agent-ten.vercel.app",
        "https://astro-agent.vercel.app",
        os.getenv("FRONTEND_URL", "https://placeholder.vercel.app"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(chart.router, prefix="/api")

if os.getenv("ENV") == "development":
    app.include_router(eval_routes.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "gemini_api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        "groq_api_key_configured": bool(os.getenv("GROQ_API_KEY")),
    }