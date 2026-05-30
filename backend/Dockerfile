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

# Make the entire application directory fully writable (fixes sqlite3/chromadb permissions for non-root users on Render)
RUN chmod -R 777 /app

# Ingestion is bypassed at build-time to avoid API Key errors when environment variables are hidden.
# Ingestion is run dynamically on container startup under API lifespan if chroma_store is missing.

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]