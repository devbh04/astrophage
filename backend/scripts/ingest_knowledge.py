"""
Knowledge Ingestion Script.

Reads all .md files from backend/knowledge_base/, chunks them into large
sections, embeds with gemini-embedding-001 (RETRIEVAL_DOCUMENT, 768 dims),
and upserts into the Qdrant Cloud collection.

Auto-creates the collection if it doesn't exist.

Usage:
    cd backend
    uv run python scripts/ingest_knowledge.py

Embedding parity with knowledge_lookup.py:
    - Same model: gemini-embedding-001 (from EMBEDDING_MODEL env var)
    - Same dimensionality: 768
    - Same normalization: L2 normalize for gemini-embedding-001
    - Ingest uses task_type=RETRIEVAL_DOCUMENT
    - Lookup uses task_type=RETRIEVAL_QUERY
"""

import math
import os
import sys
import time
import uuid
from pathlib import Path

# ── Add project root to path so we can import app.config ───────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import get_settings

# ── Constants ──────────────────────────────────────────────────

EMBED_DIM = 768                  # must match knowledge_lookup.py
CHUNK_SIZE = 2000                # characters per chunk (large to reduce API calls)
CHUNK_OVERLAP = 300              # overlap so we don't split mid-sentence
BATCH_SIZE = 10                  # embed up to 10 texts per API call
RATE_LIMIT_WAIT = 70             # seconds to wait on 429


# ── Helpers ────────────────────────────────────────────────────

def chunk_markdown(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split markdown text into overlapping chunks, preferring section
    boundaries (## headings) as split points when possible.
    """
    sections: list[str] = []
    current = ""

    for line in text.split("\n"):
        # Split at ## headings if current chunk is big enough
        if line.startswith("## ") and len(current) >= chunk_size // 2:
            sections.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        sections.append(current.strip())

    # Now break any oversized sections into character-level chunks
    chunks: list[str] = []
    for section in sections:
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            start = 0
            while start < len(section):
                end = start + chunk_size
                chunks.append(section[start:end])
                start += chunk_size - overlap

    return [c for c in chunks if len(c.strip()) > 50]  # drop tiny fragments


def l2_normalize(values: list[float]) -> list[float]:
    """L2 normalize a vector (required for gemini-embedding-001 at non-3072 dims)."""
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]


def embed_batch_with_retry(
    client: genai.Client,
    texts: list[str],
    model: str,
) -> list[list[float]]:
    """
    Embed a batch of texts with RETRIEVAL_DOCUMENT task type.
    Retries on rate limit (429) after waiting RATE_LIMIT_WAIT seconds.
    """
    while True:
        try:
            config = types.EmbedContentConfig(
                output_dimensionality=EMBED_DIM,
                task_type="RETRIEVAL_DOCUMENT",
            )
            resp = client.models.embed_content(
                model=model,
                contents=texts,
                config=config,
            )

            vectors: list[list[float]] = []
            for emb in resp.embeddings:
                vals = list(emb.values)
                if len(vals) > EMBED_DIM:
                    vals = vals[:EMBED_DIM]
                # L2 normalize for gemini-embedding-001 with non-3072 dims
                if "embedding-001" in model:
                    vals = l2_normalize(vals)
                vectors.append(vals)

            return vectors

        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "resource" in err_str or "quota" in err_str or "rate" in err_str:
                print(f"  ⏳ Rate limited. Waiting {RATE_LIMIT_WAIT}s before retry...")
                time.sleep(RATE_LIMIT_WAIT)
                continue
            else:
                raise


# ── Main ───────────────────────────────────────────────────────

def main():
    settings = get_settings()

    # Validate config
    if not settings.google_api_key:
        print("❌ GOOGLE_API_KEY not set in .env")
        sys.exit(1)
    if not settings.qdrant_url or not settings.qdrant_api_key:
        print("❌ QDRANT_URL or QDRANT_API_KEY not set in .env")
        sys.exit(1)

    model = settings.embedding_model or "gemini-embedding-001"
    collection = settings.qdrant_collection or "astrophage_knowledge"

    print(f"🔧 Embedding model:   {model}")
    print(f"🔧 Vector dimensions: {EMBED_DIM}")
    print(f"🔧 Qdrant collection: {collection}")
    print(f"🔧 Chunk size:        {CHUNK_SIZE} chars (overlap {CHUNK_OVERLAP})")
    print()

    # Initialize clients
    ai_client = genai.Client(api_key=settings.google_api_key)
    qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    # ── Create collection if it doesn't exist ───────────────────
    existing = [c.name for c in qdrant.get_collections().collections]
    if collection in existing:
        print(f"✅ Collection '{collection}' exists. Will upsert (overwrite duplicates).")
        # Wipe existing data so we get a clean re-ingest
        qdrant.delete_collection(collection)
        print(f"   Deleted old data. Recreating...")

    qdrant.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )
    print(f"✅ Collection '{collection}' ready ({EMBED_DIM}d, cosine).\n")

    # ── Load and chunk all markdown files ───────────────────────
    kb_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
    md_files = sorted(kb_dir.glob("*.md"))

    if not md_files:
        print(f"❌ No .md files found in {kb_dir}")
        sys.exit(0)

    print(f"📂 Found {len(md_files)} knowledge files:\n")

    all_chunks: list[dict] = []  # {text, source, chunk_index}

    for fpath in md_files:
        text = fpath.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)
        print(f"  📄 {fpath.name} → {len(chunks)} chunks ({len(text):,} chars)")
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": fpath.name,
                "chunk_index": i,
            })

    print(f"\n📊 Total chunks: {len(all_chunks)}")
    total_batches = math.ceil(len(all_chunks) / BATCH_SIZE)
    print(f"📊 Batches ({BATCH_SIZE}/batch): {total_batches}")
    print()

    # ── Embed in batches and upsert ─────────────────────────────
    points: list[PointStruct] = []

    for batch_idx in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = (batch_idx // BATCH_SIZE) + 1
        print(f"  🔄 Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ", flush=True)

        texts = [c["text"] for c in batch]
        vectors = embed_batch_with_retry(ai_client, texts, model)

        for chunk_meta, vector in zip(batch, vectors):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk_meta["text"],
                        "source": chunk_meta["source"],
                        "chunk_index": chunk_meta["chunk_index"],
                    },
                )
            )

        print("✅")

    # ── Upsert all points to Qdrant ─────────────────────────────
    if points:
        print(f"\n⬆️  Upserting {len(points)} vectors to Qdrant...", end=" ", flush=True)
        # Upsert in batches of 100 to avoid payload size limits
        for i in range(0, len(points), 100):
            qdrant.upsert(
                collection_name=collection,
                points=points[i : i + 100],
            )
        print("✅")

    # ── Verify ──────────────────────────────────────────────────
    info = qdrant.get_collection(collection)
    print(f"\n🎉 Done! Collection '{collection}' now has {info.points_count} vectors.")
    print(f"   Dimensions: {EMBED_DIM}, Distance: cosine")
    print(f"   Ready for knowledge_lookup queries.\n")


if __name__ == "__main__":
    main()
