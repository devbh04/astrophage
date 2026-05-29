"""
Knowledge ingestion CLI.

Walks ``backend/knowledge_base/*.md``, splits each file into chunks of at most
600 tokens with 100-token overlap, embeds each chunk with
``text-embedding-004``, and upserts the chunks into the Qdrant collection
``astrophage_knowledge``.

Run:
    uv run python scripts/ingest_knowledge.py
    uv run python scripts/ingest_knowledge.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib

import re
from pathlib import Path
from typing import Iterable, NamedTuple

# We avoid hard top-level imports that require credentials so the module
# can be imported in test environments without network.
try:
    from app.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # type: ignore


CHUNK_TOKENS = 600
OVERLAP_TOKENS = 100
COLLECTION_NAME = "astrophage_knowledge"
EMBED_DIM = 768


class Chunk(NamedTuple):
    text: str
    source: str
    heading_path: list[str]
    chunk_index: int


# ── Chunking ────────────────────────────────────────────────────


_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def tokenize(text: str) -> list[str]:
    """Crude whitespace+punctuation tokenizer (kept dependency-free)."""
    return _TOKEN_RE.findall(text)


def detokenize(tokens: list[str]) -> str:
    return " ".join(tokens)


def split_by_headings(markdown: str) -> list[tuple[list[str], str]]:
    """Split markdown into (heading_path, body) pairs using ATX headings."""
    sections: list[tuple[list[str], str]] = []
    current_path: list[str] = []
    current_lines: list[str] = []
    heading_stack: list[tuple[int, str]] = []

    def flush():
        if current_lines:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((list(current_path), body))

    for line in markdown.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            current_lines = []
            level = len(m.group(1))
            heading = m.group(2).strip()
            # Truncate stack to enclosing levels
            heading_stack = [(lvl, txt) for lvl, txt in heading_stack if lvl < level]
            heading_stack.append((level, heading))
            current_path = [txt for _, txt in heading_stack]
        else:
            current_lines.append(line)
    flush()
    return sections


def chunk_markdown(
    text: str,
    *,
    source: str,
    max_tokens: int = CHUNK_TOKENS,
    overlap: int = OVERLAP_TOKENS,
) -> list[Chunk]:
    """Chunk markdown by headings then into ≤ `max_tokens` windows with overlap."""
    sections = split_by_headings(text)
    chunks: list[Chunk] = []
    chunk_idx = 0
    for heading_path, body in sections:
        tokens = tokenize(body)
        if not tokens:
            continue
        if len(tokens) <= max_tokens:
            chunks.append(Chunk(detokenize(tokens), source, heading_path, chunk_idx))
            chunk_idx += 1
            continue
        # Sliding window with overlap
        i = 0
        step = max(1, max_tokens - overlap)
        while i < len(tokens):
            window = tokens[i : i + max_tokens]
            if not window:
                break
            chunks.append(Chunk(detokenize(window), source, heading_path, chunk_idx))
            chunk_idx += 1
            if i + max_tokens >= len(tokens):
                break
            i += step
    return chunks


def stable_chunk_id(source: str, chunk_index: int) -> str:
    """Deterministic chunk id derived from source + chunk_index."""
    h = hashlib.sha1(f"{source}:{chunk_index}".encode("utf-8")).hexdigest()
    return h


# ── Embedding + upsert ──────────────────────────────────────────


async def _embed(client, text: str) -> list[float]:
    resp = client.models.embed_content(model="text-embedding-004", contents=[text])
    # google.genai returns ``EmbedContentResponse`` with `embeddings[0].values`.
    if hasattr(resp, "embeddings") and resp.embeddings:
        return list(resp.embeddings[0].values)
    if isinstance(resp, dict) and "embeddings" in resp:
        return list(resp["embeddings"][0]["values"])
    raise RuntimeError("Unexpected embed_content response")


async def ingest_directory(
    md_dir: Path,
    *,
    dry_run: bool = False,
    google_client=None,
    qdrant_client=None,
) -> dict:
    """
    Ingest every .md file under `md_dir`.

    `google_client` and `qdrant_client` are injectable for testing — when
    None, real clients are constructed lazily.

    Returns a summary ``{files, chunks, upserted}`` dict.
    """
    files = sorted(p for p in md_dir.glob("*.md") if p.is_file())
    all_chunks: list[Chunk] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        all_chunks.extend(chunk_markdown(text, source=path.name))

    if dry_run:
        return {"files": len(files), "chunks": len(all_chunks), "upserted": 0, "dry_run": True}

    # Lazy client construction
    if google_client is None:
        from google import genai  # type: ignore
        settings = get_settings() if get_settings else None
        api_key = settings.google_api_key if settings else os.environ.get("GOOGLE_API_KEY", "")
        google_client = genai.Client(api_key=api_key)

    if qdrant_client is None:
        from qdrant_client import AsyncQdrantClient  # type: ignore
        from qdrant_client.http.models import Distance, VectorParams  # type: ignore
        settings = get_settings() if get_settings else None
        url = settings.qdrant_url if settings else os.environ.get("QDRANT_URL", "")
        api_key = settings.qdrant_api_key if settings else os.environ.get("QDRANT_API_KEY", "")
        qdrant_client = AsyncQdrantClient(url=url, api_key=api_key)
        # Create collection if it doesn't exist
        try:
            await qdrant_client.get_collection(COLLECTION_NAME)
        except Exception:
            await qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
            )

    from qdrant_client.http.models import PointStruct  # type: ignore

    points = []
    for chunk in all_chunks:
        vec = await _embed(google_client, chunk.text)
        points.append(
            PointStruct(
                id=stable_chunk_id(chunk.source, chunk.chunk_index),
                vector=vec,
                payload={
                    "text": chunk.text,
                    "source": chunk.source,
                    "heading_path": chunk.heading_path,
                    "chunk_index": chunk.chunk_index,
                },
            )
        )
    if points:
        await qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

    return {"files": len(files), "chunks": len(all_chunks), "upserted": len(points), "dry_run": False}


def _default_md_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "knowledge_base"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest the AstroAgent knowledge base into Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Don't call embedding or Qdrant APIs")
    parser.add_argument("--md-dir", type=Path, default=_default_md_dir(), help="Markdown source directory")
    args = parser.parse_args(list(argv) if argv is not None else None)

    summary = asyncio.run(ingest_directory(args.md_dir, dry_run=args.dry_run))
    if args.dry_run:
        print(f"[dry-run] files={summary['files']} chunks={summary['chunks']}")
    else:
        print(
            f"ingested files={summary['files']} chunks={summary['chunks']} "
            f"upserted={summary['upserted']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "Chunk",
    "chunk_markdown",
    "stable_chunk_id",
    "ingest_directory",
    "main",
    "tokenize",
    "split_by_headings",
    "COLLECTION_NAME",
    "EMBED_DIM",
]
