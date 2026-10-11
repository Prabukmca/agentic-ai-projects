from pathlib import Path

from generic_rag_chatbot import FolderDocumentLoader, GenericRAGChatbot


CATALOGUE_FOLDER = Path(__file__).with_name("catalogue_documents")


def build_chatbot() -> GenericRAGChatbot:
    return GenericRAGChatbot(CATALOGUE_FOLDER)


def retrieved_text(chatbot: GenericRAGChatbot, question: str) -> str:
    return "\n".join(document.page_content for document in chatbot._retrieve(question, limit=10)).lower()


def test_pdf_catalogue_is_loaded_as_generic_documents():
    documents = FolderDocumentLoader(CATALOGUE_FOLDER).load()

    assert documents
    assert all(document.metadata["source"].endswith(".pdf") for document in documents)
    assert any("classic diamond ring" in document.page_content.lower() for document in documents)


def test_price_question_retrieves_source_context():
    chatbot = build_chatbot()
    source_text = retrieved_text(chatbot, "What is the price of the Ruby Solitaire Ring?")

    assert "ruby solitaire ring" in source_text
    assert "98,500" in source_text or "98500" in source_text


def test_diamond_question_retrieves_all_relevant_source_text():
    chatbot = build_chatbot()
    source_text = retrieved_text(chatbot, "Show me diamond products")

    assert "classic diamond ring" in source_text
    assert "diamond stud earrings" in source_text
    assert "lotus pendant" in source_text


def test_material_question_retrieves_source_context():
    chatbot = build_chatbot()
    source_text = retrieved_text(chatbot, "Which products are made of 22K gold?")

    assert "22k gold" in source_text
    assert "ruby solitaire ring" in source_text
    assert "emerald choker" in source_text


def test_product_list_request_has_names_only_output_instruction(monkeypatch):
    chatbot = build_chatbot()
    captured = {}

    class FakeResponse:
        output_text = '{"items": ["Ruby Solitaire Ring"]}'

    class FakeResponses:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["input"][0]["content"]
            return FakeResponse()

    class FakeClient:
        responses = FakeResponses()

    monkeypatch.setattr("generic_rag_chatbot.OpenAI", lambda **kwargs: FakeClient())
    answer = chatbot.answer("Show me the products of 22K gold")

    assert answer == "- Ruby Solitaire Ring"
    assert 'return a JSON object exactly in this shape' in captured["prompt"]
    assert "include every matching item exactly once" in captured["prompt"]


def test_category_and_stock_questions_use_source_retrieval():
    chatbot = build_chatbot()

    earrings_text = retrieved_text(chatbot, "What are earrings available?")
    stock_text = retrieved_text(chatbot, "Show me out of stock products")

    assert "diamond stud earrings" in earrings_text
    assert "daily wear gold earrings" in earrings_text
    assert "ruby solitaire ring" in stock_text
    assert "emerald cuff bracelet" in stock_text


def test_price_range_question_retrieves_catalogue_source():
    chatbot = build_chatbot()
    source_text = retrieved_text(chatbot, "Show me jewels below Rs. 50000")

    assert "om symbol pendant" in source_text
    assert "48,000" in source_text or "48000" in source_text


def test_out_of_stock_question_retrieves_alternative_source_context():
    chatbot = build_chatbot()
    source_text = retrieved_text(chatbot, "What is the price of the Ruby Solitaire Ring?")

    assert "ruby solitaire ring" in source_text
    assert "out of stock" in source_text
    assert "classic diamond ring" in source_text


def test_indian_price_units_retrieve_catalogue_source():
    chatbot = build_chatbot()

    lakh_text = retrieved_text(chatbot, "Show me a jewel below 1 lakh")
    thousands_text = retrieved_text(chatbot, "Show me jewels below 50 thousands rupees")

    assert "om symbol pendant" in lakh_text
    assert "48,000" in lakh_text or "48000" in lakh_text
    assert "om symbol pendant" in thousands_text


def test_weight_question_retrieves_weight_source_field():
    chatbot = build_chatbot()
    source_text = retrieved_text(chatbot, "Show me the least weight product")

    assert "weight:" in source_text
    assert "ruby solitaire ring" in source_text


def test_follow_up_retrieval_uses_buffer_memory():
    chatbot = build_chatbot()

    chatbot.answer("Show me diamond products")
    follow_up_documents = chatbot._retrieve("What is the price of the ring?", limit=10)
    follow_up_text = "\n".join(document.page_content for document in follow_up_documents).lower()

    assert len(chatbot.history) == 1
    assert "show me diamond products" in chatbot.history[0]["question"].lower()
    assert "classic diamond ring" in follow_up_text
    assert "diamond stud earrings" in follow_up_text


def test_answer_uses_only_retrieved_source_context(monkeypatch):
    chatbot = build_chatbot()
    captured = {}

    def fake_answer(question, documents):
        captured["question"] = question
        captured["documents"] = documents
        return chatbot._source_context(documents)

    monkeypatch.setattr(chatbot, "_answer_from_sources", fake_answer)
    answer = chatbot.answer("What is the price of the Pearl Necklace?")

    assert captured["question"] == "What is the price of the Pearl Necklace?"
    assert captured["documents"]
    assert "pearl necklace" in answer.lower()
    assert len(chatbot.history) == 1
