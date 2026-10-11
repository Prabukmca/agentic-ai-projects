from pathlib import Path

import ornativa_chatbot
from ornativa_chatbot import UniversalDocumentAgent


CATALOGUE_FOLDER = Path(__file__).with_name("catalogue_documents")


def build_agent(monkeypatch) -> UniversalDocumentAgent:
    """Build the active agent without making embedding or LLM requests."""
    monkeypatch.setattr(ornativa_chatbot, "OpenAIEmbeddings", None)
    agent = UniversalDocumentAgent(CATALOGUE_FOLDER)
    agent.planner.client = None
    return agent


def test_22k_product_query_returns_names_only(monkeypatch):
    agent = build_agent(monkeypatch)

    answer = agent.answer("show me 22k gold products")

    assert "Ruby Solitaire Ring" in answer
    assert "Emerald Choker" in answer
    assert "Price:" not in answer
    assert "Stock:" not in answer
    assert "Name:" not in answer


def test_misspelled_22k_earrings_query_filters_by_category(monkeypatch):
    agent = build_agent(monkeypatch)

    answer = agent.answer("show me 22k gold earrnings")

    assert answer == "- Daily Wear Gold Earrings"


def test_22k_earrings_query_does_not_match_ring_substring(monkeypatch):
    agent = build_agent(monkeypatch)

    answer = agent.answer("show me 22k gold earrings")

    assert answer == "- Daily Wear Gold Earrings"


def test_18k_rings_query_does_not_include_earrings(monkeypatch):
    agent = build_agent(monkeypatch)

    answer = agent.answer("show me 18k gold rings")

    assert answer == "- Classic Diamond Ring"


def test_model_plan_cannot_drop_an_explicit_category_constraint(monkeypatch):
    agent = build_agent(monkeypatch)

    class IncompletePlanner:
        def plan(self, question, fields, previous_ids):
            return {
                "operation": "filter",
                "conditions": [{"field": "material", "operator": "contains", "value": "22K Gold"}],
                "sort": None,
                "output_fields": ["name"],
            }

    agent.planner = IncompletePlanner()
    fallback_plan = agent.planner
    original_plan = ornativa_chatbot.QueryPlanner._merge_explicit_constraints

    # Exercise the production merger with an intentionally incomplete model plan.
    planner = ornativa_chatbot.QueryPlanner()
    planner.client = None
    schema = agent._catalogue_schema()
    expected = planner._fallback("show me 22k gold earrnings", sorted(schema), [], schema)
    merged = original_plan(fallback_plan.plan("", [], []), expected)

    assert any(condition["field"] == "category" for condition in merged["conditions"])


def test_fallback_resolves_values_from_an_arbitrary_catalogue_schema():
    planner = ornativa_chatbot.QueryPlanner()
    schema = {"name": ["Atlas Pro"], "product_type": ["Laptop", "Camera"]}

    plan = planner._fallback("show me laptops", list(schema), [], schema)

    assert plan["conditions"] == [
        {"field": "product_type", "operator": "eq", "value": "Laptop"}
    ]


def test_highest_price_is_scoped_to_the_previous_selection(monkeypatch):
    agent = build_agent(monkeypatch)
    agent.answer("show me 22k gold products")
    selected_ids = set(agent.last_record_ids)

    answer = agent.answer("show me highest price product from these list")

    assert answer == "- Emerald Choker"
    assert agent.last_record_ids
    assert set(agent.last_record_ids).issubset(selected_ids)
    assert "Price:" not in answer


def test_least_weight_is_scoped_to_the_previous_selection(monkeypatch):
    agent = build_agent(monkeypatch)
    agent.answer("show me 22k gold products")
    selected_ids = set(agent.last_record_ids)

    answer = agent.answer("show me least weight product from these list")

    assert answer == "- Ruby Solitaire Ring"
    assert set(agent.last_record_ids).issubset(selected_ids)


def test_global_weight_rankings_do_not_reuse_the_previous_selection(monkeypatch):
    agent = build_agent(monkeypatch)

    highest = agent.answer("what is highest weight product?")
    lowest = agent.answer("what is the least weight product?")

    assert highest == "- Emerald Choker"
    assert lowest == "- Ruby Solitaire Ring"


def test_explicit_price_follow_up_reads_only_the_price_field(monkeypatch):
    agent = build_agent(monkeypatch)
    agent.answer("show me 22k gold products")

    answer = agent.answer("show me the price details of these products")

    assert "Ruby Solitaire Ring" in answer
    assert "Price:" in answer
    assert "Stock:" not in answer
    assert "Out of Stock" not in answer


def test_singular_reference_uses_the_immediately_previous_selection(monkeypatch):
    agent = build_agent(monkeypatch)
    agent.answer("show me 18k gold rings")

    answer = agent.answer("show me the price for this one")

    assert answer == "- Classic Diamond Ring: Price: ₹135,000"


def test_unscoped_detail_request_uses_the_immediately_previous_selection(monkeypatch):
    agent = build_agent(monkeypatch)
    agent.answer("show me 22k gold earrings")

    answer = agent.answer("show me price details")

    assert answer == "- Daily Wear Gold Earrings: Price: ₹55,000"


def test_unqualified_details_request_asks_for_fields(monkeypatch):
    agent = build_agent(monkeypatch)
    agent.answer("show me 22k gold products")

    answer = agent.answer("show me details of these products")

    assert answer == "Which product details would you like: price, weight, material, category, or stock?"


def test_combined_category_material_and_price_filter_is_deterministic(monkeypatch):
    agent = build_agent(monkeypatch)

    answer = agent.answer("any earrings, 22k gold, above Rs.500000?")

    assert answer == "I could not find supporting information in the document catalogue."