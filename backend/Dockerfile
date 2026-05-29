FROM python:3.11-slim

# Build tools required by pyswisseph
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pre-build the ChromaDB collection from knowledge base docs
# (If chroma_store already exists on mounted disk, this is a no-op due to upsert)
RUN python knowledge_base/ingest.py || echo "Ingest skipped (may run on first start)"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]