import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


load_dotenv()


def load_pdf_documents(folder_path: str):
    folder = Path(folder_path)
    docs = []
    pdf_files = sorted(folder.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {folder}")

    for pdf_file in pdf_files:
        try:
            try:
                loader = PyMuPDFLoader(str(pdf_file))
                file_docs = loader.load()
            except Exception:
                loader = PyPDFLoader(str(pdf_file))
                file_docs = loader.load()

            for doc in file_docs:
                doc.metadata["source"] = pdf_file.name
                if doc.page_content.strip():
                    docs.append(doc)

            print(f"Loaded {len(file_docs)} pages from {pdf_file.name}")
        except Exception as exc:
            print(f"Skipping {pdf_file.name}: {exc}")

    return docs


def build_vector_store(doc_dir: str, persist_path: str):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing. Add it to a .env file or export it.")

    raw_docs = load_pdf_documents(doc_dir)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(raw_docs)
    print(f"Created {len(chunks)} chunks from {len(raw_docs)} pages.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(persist_path)
    print(f"Saved vector store to {persist_path}")
    return vectorstore


def main():
    parser = argparse.ArgumentParser(description="Ingest insurance PDFs into a FAISS vector store.")
    parser.add_argument("--doc-dir", default="./documents", help="Folder containing the PDF documents")
    parser.add_argument("--persist-path", default="./insurance_vectorstore", help="Directory for the FAISS index")
    args = parser.parse_args()

    build_vector_store(args.doc_dir, args.persist_path)


if __name__ == "__main__":
    main()
