from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from langchain_core.documents import Document
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover
    Document = None
    FAISS = None
    OpenAIEmbeddings = None
    RecursiveCharacterTextSplitter = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class FolderDocumentLoader:
    """Loads text from every PDF in a folder without assuming a document schema."""

    def __init__(self, source_folder: str | Path):
        self.source_folder = Path(source_folder)

    def load(self) -> List[Document]:
        if PdfReader is None or Document is None:
            raise ImportError("pypdf and LangChain document dependencies are required.")
        if not self.source_folder.is_dir():
            raise FileNotFoundError(f"Document folder not found: {self.source_folder}")

        documents = []
        for pdf_path in sorted(self.source_folder.glob("*.pdf")):
            reader = PdfReader(str(pdf_path))
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": pdf_path.name,
                                "page": page_number,
                            },
                        )
                    )
        if not documents:
            raise ValueError(f"No readable PDF content found in {self.source_folder}")
        return documents


class GenericRAGChatbot:
    """Schema-independent RAG chatbot grounded only in retrieved PDF content."""

    def __init__(self, source_folder: str | Path, require_vector_store: bool = True):
        self.source_folder = Path(source_folder)
        self.store_folder = self.source_folder / "generic_faiss_store"
        self.history: List[Dict[str, str]] = []
        self.vector_store = self._ensure_vector_store(require_vector_store)

    def _source_fingerprint(self) -> str:
        """Fingerprint the current PDF corpus so an old FAISS index is never reused."""
        digest = hashlib.sha256()
        for pdf_path in sorted(self.source_folder.glob("*.pdf")):
            digest.update(pdf_path.name.encode("utf-8"))
            digest.update(pdf_path.read_bytes())
        return digest.hexdigest()

    def _ensure_vector_store(self, required: bool):
        if not (FAISS and OpenAIEmbeddings and RecursiveCharacterTextSplitter):
            if required:
                raise RuntimeError("FAISS, OpenAI embeddings, and text splitters are required.")
            return None
        if not os.getenv("OPENAI_API_KEY"):
            if required:
                raise RuntimeError("OPENAI_API_KEY is required to build the vector store.")
            return None

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        index_file = self.store_folder / "index.faiss"
        signature_file = self.store_folder / "source.sha256"
        current_signature = self._source_fingerprint()

        # Reuse an index only when it was built from exactly this PDF corpus.
        # Otherwise a stale index can silently return products from an older PDF.
        if index_file.exists() and signature_file.exists():
            try:
                if signature_file.read_text().strip() == current_signature:
                    return FAISS.load_local(
                        str(self.store_folder),
                        embeddings,
                        allow_dangerous_deserialization=True,
                    )
            except Exception:
                pass

        documents = FolderDocumentLoader(self.source_folder).load()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_documents(documents)
        self.store_folder.mkdir(parents=True, exist_ok=True)
        store = FAISS.from_documents(chunks, embeddings)
        store.save_local(str(self.store_folder))
        signature_file.write_text(current_signature)
        return store

    def _is_list_request(self, question: str) -> bool:
        """Detect requests asking for product names/items, not arbitrary details.

        Do NOT classify every "show me ..." question as a list request.
        For example, "show me the price details of these products" is a
        detail/field request and must not be converted into a names-only list.
        """
        q = question.lower()
        return (
            "list" in q
            or bool(re.search(r"\ball\b", q))
            or any(phrase in q for phrase in [
                "which products",
                "which items",
                "what products",
                "what items",
            ])
        )

    def _is_price_request(self, question: str) -> bool:
        q = question.lower()
        return any(term in q for term in [
            "price", "pricing", "cost", "costs", "how much", "amount",
        ])

    def _catalog_records(self, documents: List[Any]) -> List[Dict[str, str]]:
        """Parse ProductID/Name/Material/Price/Stock fields from catalogue text."""
        records: List[Dict[str, str]] = []
        seen = set()
        for doc in documents:
            for record in re.findall(
                r"ProductID:\s*.*?(?=ProductID:|\Z)",
                doc.page_content,
                flags=re.IGNORECASE | re.DOTALL,
            ):
                fields = {}
                for field in ["ProductID", "Name", "Category", "Material", "Weight", "Price", "Stock"]:
                    m = re.search(
                        rf"\b{field}:\s*(.*?)(?=\s+(?:ProductID|Name|Category|Material|Weight|Price|Stock):|$)",
                        record,
                        flags=re.IGNORECASE | re.DOTALL,
                    )
                    if m:
                        fields[field.lower()] = re.sub(r"\s+", " ", m.group(1)).strip()
                name = fields.get("name", "")
                if name and name.lower() not in seen:
                    records.append(fields)
                    seen.add(name.lower())
        return records

    def _referenced_product_names(self) -> List[str]:
        """Get product names from the immediately preceding assistant list."""
        if not self.history:
            return []
        previous_answer = self.history[-1].get("answer", "")
        names = []
        for line in previous_answer.splitlines():
            m = re.match(r"\s*-\s*(.+?)\s*$", line)
            if m:
                names.append(m.group(1).strip())
        return names

    def _deterministic_price_details(self, question: str, documents: List[Any]) -> str | None:
        """Return verified prices for products explicitly or contextually referenced."""
        if not self._is_price_request(question):
            return None

        names = self._referenced_product_names() if re.search(
            r"\b(these|those|them|the products|the items)\b", question, re.IGNORECASE
        ) else []
        records = self._catalog_records(documents)
        if not names:
            # For an explicit product-name price query, match names appearing in
            # the question. This avoids asking the LLM to invent the mapping.
            q = question.lower()
            names = [r["name"] for r in records if r.get("name", "").lower() in q]

        if not names:
            return None

        by_name = {r.get("name", "").lower(): r for r in records}
        lines = []
        missing = []
        for name in names:
            record = by_name.get(name.lower())
            if record and record.get("price"):
                lines.append(f"- {record['name']}: ₹{record['price']}")
            else:
                missing.append(name)

        if missing:
            return None
        return "\n".join(lines) if lines else None

    def _retrieve(self, question: str, limit: int = 8) -> List[Any]:
        if self.vector_store is None:
            return []

        # Exhaustive list queries must not use conversational history or top-k
        # semantic retrieval. Both can hide valid matching records.
        # Follow-ups referring to "these products" depend on the immediately
        # preceding result set. Retrieve the whole catalogue so no referenced
        # product's fields are lost to semantic top-k retrieval.
        contextual_followup = bool(self.history) and bool(
            re.search(r"\b(these|those|them|the products|the items)\b", question, re.IGNORECASE)
        )

        if self._is_list_request(question) or contextual_followup:
            try:
                total = len(self.vector_store.docstore._dict)
            except Exception:
                total = limit
            return self.vector_store.similarity_search(question, k=max(total, limit))

        recent_questions = " ".join(item["question"] for item in self.history[-3:])
        retrieval_query = f"{recent_questions} {question}".strip()
        return self.vector_store.similarity_search(retrieval_query, k=limit)

    def _source_context(self, documents: List[Any]) -> str:
        return "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'unknown')}, page: {doc.metadata.get('page', '?')}]\n"
            f"{doc.page_content}"
            for doc in documents
        )

    def _deterministic_catalog_list(self, question: str, documents: List[Any]) -> List[str] | None:
        """Handle exact material filters without asking the LLM to infer completeness.

        When the source uses ProductID/Name/Material records (as the supplied
        jewellery catalogue does), an explicit '<number>K Gold' filter can be
        answered deterministically from the source records.
        """
        match = re.search(r"\b(\d{1,2}k\s+gold)\b", question, re.IGNORECASE)
        if not match:
            return None

        wanted_material = re.sub(r"\s+", " ", match.group(1)).lower()
        records = []
        for doc in documents:
            # A record starts at ProductID and ends immediately before the next
            # ProductID (or the end of the chunk).
            records.extend(
                re.findall(
                    r"ProductID:\s*.*?(?=ProductID:|\Z)",
                    doc.page_content,
                    flags=re.IGNORECASE | re.DOTALL,
                )
            )

        if not records:
            return None

        results = []
        seen = set()
        for record in records:
            name_match = re.search(r"\bName:\s*(.*?)(?=\s+Category:|\s+Material:|\s+Weight:|\s+Price:|\s+Stock:|$)", record, re.IGNORECASE | re.DOTALL)
            material_match = re.search(r"\bMaterial:\s*(.*?)(?=\s+Weight:|\s+Price:|\s+Stock:|$)", record, re.IGNORECASE | re.DOTALL)
            if not name_match or not material_match:
                continue
            name = re.sub(r"\s+", " ", name_match.group(1)).strip()
            material = re.sub(r"\s+", " ", material_match.group(1)).strip().lower()
            if wanted_material in material and name.lower() not in seen:
                results.append(name)
                seen.add(name.lower())
        return results

    def _answer_from_sources(self, question: str, documents: List[Any]) -> str:
        if not documents:
            return "I could not find supporting information in the document catalogue."
        # Exact catalogue filters should never depend on LLM retrieval or
        # generation. This is both faster and guarantees completeness.
        # Field/detail requests must be handled before list formatting.
        # This prevents a follow-up such as "show me the price details of
        # these products" from being reduced to the previous product names.
        deterministic_prices = self._deterministic_price_details(question, documents)
        if deterministic_prices is not None:
            return deterministic_prices

        if self._is_list_request(question):
            deterministic_items = self._deterministic_catalog_list(question, documents)
            if deterministic_items is not None:
                if not deterministic_items:
                    return "I could not find matching products in the document catalogue."
                return "\n".join(f"- {item}" for item in deterministic_items)

        if not OpenAI or not os.getenv("OPENAI_API_KEY"):
            return "Retrieved source context:\n\n" + self._source_context(documents)

        history = "\n".join(
            f"User: {turn['question']}\nAssistant: {turn['answer']}"
            for turn in self.history[-5:]
        )
        is_list_request = self._is_list_request(question)
        list_instruction = (
            "For this list request, return a JSON object exactly in this shape: "
            '{"items": ["every matching item name"]}. Scan every retrieved source line and include '
            "every matching item exactly once. Do not summarize or omit matching items."
            if is_list_request
            else "Return a concise natural-language answer."
        )
        prompt = f"""You are a document-grounded assistant.
Answer the user's question using only the retrieved source context below.
The source context is authoritative. Do not invent, infer, or add facts that are not present.
Use conversation history only to resolve references such as 'they' or 'that product'.
If the source context does not support an answer, say: I could not find supporting information in the document catalogue.
Be concise and directly answer the question.
{list_instruction}
When the user asks a follow-up for details, use the previous conversation context and provide only the requested fields.

Retrieved source context:
{self._source_context(documents)}

Conversation history:
{history}

User question:
{question}
"""
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.responses.create(
                model="gpt-4o-mini",
                input=[{"role": "user", "content": prompt}],
            )
            answer = response.output_text.strip()
            if is_list_request:
                try:
                    payload = json.loads(answer)
                    items = payload.get("items", [])
                    if isinstance(items, list) and all(isinstance(item, str) for item in items):
                        # Every returned name must literally exist in the
                        # retrieved source. This blocks invented product names.
                        source_text = self._source_context(documents).lower()
                        verified = []
                        seen = set()
                        for item in items:
                            item = item.strip()
                            key = item.lower()
                            if item and key in source_text and key not in seen:
                                verified.append(item)
                                seen.add(key)
                        return "\n".join(f"- {item}" for item in verified)
                except (json.JSONDecodeError, AttributeError, TypeError):
                    pass

                # Never fall back to an unverified free-form list answer.
                return "I could not reliably extract the complete matching list from the document catalogue."
            return answer
        except Exception as error:
            raise RuntimeError(f"LLM response generation failed: {error}") from error

    def answer(self, question: str) -> str:
        """Retrieve source chunks and generate a grounded answer with buffer memory."""
        query = (question or "").strip()
        if not query:
            return "Please ask a question about the documents."
        documents = self._retrieve(query)
        answer = self._answer_from_sources(query, documents)
        self.history.append({"question": query, "answer": answer})
        return answer
