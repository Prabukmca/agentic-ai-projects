from enterprise_knowledge_ops_agent import SourceDocument, AnalystAgent

analyst = AnalystAgent()

# Create multiple sources with similar info
doc1 = SourceDocument(
    id="doc-1", title="HR Remote Work Policy", source="hr-policy.pdf",
    content="The policy allows remote work up to three days per week."
)
doc2 = SourceDocument(
    id="doc-2", title="Compliance Guidelines", source="compliance.pdf",
    content="The policy allows remote work up to three days per week, subject to approval."
)

question = "What is the remote work policy?"
result = analyst.reason(question, [doc1, doc2])

print("=" * 60)
print("MULTI-SOURCE ANSWER OUTPUT")
print("=" * 60)
print("\nANSWER:")
print(result["answer"])
print("\nCITATIONS:")
for cite in result["citations"]:
    print(f"  - {cite}")
print("\nREASONING:")
print(result["reasoning"])
print("=" * 60)
