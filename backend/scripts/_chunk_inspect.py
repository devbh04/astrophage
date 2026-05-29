"""Quick diagnostic — print chunk counts per KB file."""
from pathlib import Path
from ingest_knowledge import chunk_markdown


def main() -> None:
    total = 0
    kb = Path(__file__).resolve().parents[1] / "knowledge_base"
    for path in sorted(kb.glob("*.md")):
        chunks = chunk_markdown(path.read_text(encoding="utf-8"), source=path.name)
        print(f"{path.name:70s} {len(chunks):4d}")
        total += len(chunks)
    print(f"{'TOTAL':70s} {total:4d}")


if __name__ == "__main__":
    main()
