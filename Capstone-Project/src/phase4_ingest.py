from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class IngestResult:
    files_count: int
    chunks_count: int
    index_path: str


def load_markdown_documents(raw_docs_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for file_path in sorted(raw_docs_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        source = "unknown"
        for line in text.splitlines()[:6]:
            if line.lower().startswith("source:"):
                source = line.split(":", 1)[1].strip()
                break

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "file_name": file_path.name,
                    "source": source,
                },
            )
        )
    return docs


def build_vectorstore(raw_docs_dir: Path, vectorstore_dir: Path) -> IngestResult:
    docs = load_markdown_documents(raw_docs_dir)
    if not docs:
        raise ValueError(f"No markdown documents found in {raw_docs_dir}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(vectorstore_dir))

    manifest = {
        "documents": [doc.metadata for doc in docs],
        "files_count": len(docs),
        "chunks_count": len(chunks),
    }
    manifest_path = vectorstore_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")

    return IngestResult(
        files_count=len(docs),
        chunks_count=len(chunks),
        index_path=str(vectorstore_dir),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 4 RAG ingest")
    parser.add_argument(
        "--raw-dir",
        default="data/raw/banking_docs",
        help="Raw curated markdown documents directory relative to Capstone-Project",
    )
    parser.add_argument(
        "--vectorstore-dir",
        default="vectorstore/phase4_banking_faiss",
        help="Output vectorstore directory relative to Capstone-Project",
    )
    return parser.parse_args()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")
    load_dotenv(project_root.parent / ".env")

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing. Configure it before running Phase 4 ingest.")
        return 2

    args = parse_args()
    raw_dir = project_root / args.raw_dir
    vectorstore_dir = project_root / args.vectorstore_dir

    result = build_vectorstore(raw_dir, vectorstore_dir)
    print(
        f"Indexed {result.files_count} files into {result.chunks_count} chunks at: {result.index_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
