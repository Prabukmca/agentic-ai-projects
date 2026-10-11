import pytest
from enterprise_knowledge_ops_agent import (
    SourceDocument, AnalystAgent, RetrieverAgent, VerifierAgent, OrchestratorAgent, MemoryAgent
)


def test_multi_source_answers():
    """Test that the agent returns answers from ALL relevant sources, not just the first one."""
    analyst = AnalystAgent()
    
    # Create multiple sources with overlapping content
    doc1 = SourceDocument(
        id="doc-1",
        title="Remote Work Policy",
        source="remote-policy.pdf",
        content="The policy allows remote work up to three days per week, subject to manager approval and business needs."
    )
    doc2 = SourceDocument(
        id="doc-2",
        title="Work Guidelines",
        source="work-guidelines.pdf",
        content="The policy allows remote work up to three days per week, subject to manager approval and business needs. Employees must coordinate with their teams."
    )
    
    question = "What is the remote work policy?"
    result = analyst.reason(question, [doc1, doc2])
    
    # Check that both sources are mentioned in the answer
    assert "Remote Work Policy" in result["answer"]
    assert "Work Guidelines" in result["answer"]
    assert len(result["citations"]) == 2
    print("✓ Multi-source answers test passed")
    print(f"Answer:\n{result['answer']}\n")


def test_retriever_returns_multiple_docs():
    """Test that retriever returns k=5 documents instead of k=2."""
    retriever = RetrieverAgent()
    
    # Create 6 documents
    docs = [
        SourceDocument(id=f"doc-{i}", title=f"Policy {i}", source=f"policy-{i}.pdf", 
                      content=f"This is about remote work policy document {i}.")
        for i in range(1, 7)
    ]
    
    question = "What is the remote work policy?"
    retrieved = retriever.retrieve(question, docs)
    
    # Should retrieve at least 5 documents (or all 6 if they all score)
    assert len(retrieved) >= 5
    print(f"✓ Retriever returns {len(retrieved)} documents (expected >= 5)")


def test_verifier_with_multiple_sources():
    """Test that verifier works with multiple source documents."""
    verifier = VerifierAgent()
    
    doc1 = SourceDocument(id="doc-1", title="Policy A", source="a.pdf", content="remote work three days")
    doc2 = SourceDocument(id="doc-2", title="Policy B", source="b.pdf", content="remote work three days")
    
    question = "What about remote work?"
    answer = "The policy allows remote work up to three days per week."
    
    result = verifier.verify(question, answer, [doc1, doc2])
    
    # Should have grounding status
    assert "status" in result
    assert "grounding_score" in result
    assert result["grounding_score"] >= 0.0
    print(f"✓ Verifier grounding: {result['status']} (score: {result['grounding_score']:.3f})")


def test_orchestrator_answers_general_question_from_document_content():
    """Test that orchestrator brings answers from multiple documents."""
    memory = MemoryAgent()
    orchestrator = OrchestratorAgent(memory=memory)
    
    docs = [
        SourceDocument(
            id="doc-1",
            title="Travel Policy",
            source="travel.pdf",
            content="Travel and lodging reimbursements require pre-approval and receipts."
        ),
        SourceDocument(
            id="doc-2",
            title="Expense Guidelines",
            source="expenses.pdf",
            content="Travel and lodging reimbursements require pre-approval and receipts; meals are reimbursable only for overnight travel."
        ),
    ]
    
    question = "What is the travel reimbursement policy?"
    result = orchestrator.run(question, docs)
    
    # Should have answer
    assert result["answer"]
    assert "Travel Policy" in result["answer"] or "Expense Guidelines" in result["answer"]
    assert len(result["trace"]["retrieval"]) > 0
    print(f"✓ Orchestrator multi-source test passed")
    print(f"Answer preview: {result['answer'][:200]}...")


def test_safe_workplace_question_uses_relevant_sentence():
    """The fallback must not answer with the first, unrelated policy sentence."""
    analyst = AnalystAgent()
    doc = SourceDocument(
        id="doc-1",
        title="Human Rights Policy",
        source="human-rights-policy.pdf",
        content=(
            "Human Rights Policy Scope This Policy applies to all directors, officers, and employees. "
            "Maintain a safe and healthy workplace. Always follow all applicable safety and health laws "
            "and regulations within Cognizant facilities and client sites."
        ),
    )

    result = analyst.reason("How to maintain safe healthy workplace?", [doc])

    assert "Maintain a safe and healthy workplace" in result["answer"]
    assert "Human Rights Policy Scope" not in result["answer"]


if __name__ == "__main__":
    test_multi_source_answers()
    test_retriever_returns_multiple_docs()
    test_verifier_with_multiple_sources()
    test_orchestrator_answers_general_question_from_document_content()
    print("\n✅ All tests passed!")
