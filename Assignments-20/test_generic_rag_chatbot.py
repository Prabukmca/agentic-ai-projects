from pathlib import Path

from generic_rag_chatbot import FolderDocumentLoader, GenericRAGChatbot


def test_folder_loader_reads_all_catalogue_pdfs():
    folder = Path(__file__).with_name("catalogue_documents")
    documents = FolderDocumentLoader(folder).load()

    assert documents
    assert all(document.metadata["source"].endswith(".pdf") for document in documents)
    assert any("Classic Diamond Ring" in document.page_content for document in documents)


def test_generic_rag_chatbot_loads_persistent_vector_store():
    folder = Path(__file__).with_name("catalogue_documents")
    chatbot = GenericRAGChatbot(folder)

    assert chatbot.vector_store is not None
    assert (folder / "generic_faiss_store" / "index.faiss").exists()
    assert (folder / "generic_faiss_store" / "index.pkl").exists()