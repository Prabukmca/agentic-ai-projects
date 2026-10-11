Capstone Project: Design, Build, Evaluate an AI Agent
Introduction
In this Industry Capstone, you will work as an AI Engineer inside a
company. The organization wants to deploy an AI agent that can assist users in real
workflows — handling ambiguity, reasoning across steps, using tools, learning from
feedback, and operating safely in production.
Your responsibility is to design, build, test, iterate, and justify an AI agent as it would be
done in an industry setting, not as a one-off prototype.

Problem Statement
You must design an AI agent that supports a realistic business workflow in one chosen
industry scenario. The agent should demonstrate reliability, explainability, safety-first
behaviour, and practical usefulness for real users, with evidence through artefacts and test
logs.
Your final submission should make it clear:
• who the user is and what workflow the agent supports,
• what success looks like (criteria + metrics),
• what failures you anticipated and how you handled them,
• and why your architecture/design decisions are justified.

Scenario 1: Banking — AI Banking Support & Advisory Agent (Non-
Transactional)
Safety Requirements:
• Must refuse money movement, approvals, or legal advice.
• Must not hallucinate customer data.
• Must escalate ambiguous or high-risk cases.
• Must not store PII in logs.

Scenario 2: Customer Support — AI Support Resolution Agent
Safety Requirements:
• Must refuse unsafe or policy-violating requests.
• Must not fabricate policies.
• Must escalate sensitive or unresolved cases.
• Must not store personal data in logs.

Or Can I choose ReInsurance concepts for customer support?
-- let me know what kind of documents required for the vector store
-- we need documents for other scenarios as well correct?, I should download from online correct?

Task to be performed
You will build the agent following an industry workflow across the phases below. Your
submission must include clear evidence (screenshots/logs/tables/artefacts) for the key
capabilities.
Phase 1: Understand the Problem & Define Success
Coding: Not Required (optional)
Tools/Skills: Problem framing, user persona definition, workflow mapping, requirements
writing, success criteria, edge-case thinking, evaluation planning
• Identify the primary user persona and daily workflow
• Document the exact problem to be solved
• Define inputs, outputs, constraints, and assumptions
Write 3–5 example user questions
• Define success criteria
• List known failure cases and edge scenarios

Phase 2: Build a Basic Working Agent
Coding: Required
Tools/Skills: Python, CLI or notebook workflow, input/output handling, basic
rules/templates, logging sample runs
• Create a Python-based agent
• Handle user input and generate responses
• Demonstrate baseline limitations

Tasks
• Create a Python-based agent that accepts user input
• Implement basic response generation (rules or templates)
• Demonstrate at least 2 limitations of the baseline agent
• Log sample interactions and responses
• Explain why this version is insufficient for real users

Phase 3: Make the Agent Smarter
Coding: Required
Tools/Skills: LLM integration (provider API), prompt engineering, prompt versioning,
structured comparison of outputs, error/failure analysis
• Integrate an LLM
• Experiment with prompt strategies
• Show how behaviour changes with better prompts

Tasks
• Integrate an LLM into the agent workflow
• Design and test multiple prompt strategies
• Compare outputs across prompt variants
• Document improvements and new failure modes
• Select a default prompt strategy with justification

Phase 4: Add Knowledge & Retrieval
Coding: Required
Tools/Skills: Embeddings, semantic search, RAG concepts, text chunking, vector stores (e.g.,
Chroma/FAISS), retrieval-quality testing
• Implement embeddings and retrieval
• Enable document or data reference
• Show improvement over baseline

Tasks
• Prepare documents or datasets for embedding
• Implement semantic search using embeddings
• Connect retrieval results to agent responses
• Compare responses with and without retrieval
• Handle cases where relevant information is missing

Phase 5: Enable Tool Usage
Coding: Required
Tools/Skills: Tool/function calling, tool schemas, routing/selection logic, guardrails, error
handling, loop prevention
• Allow the agent to choose and use tools
• Demonstrate correct vs incorrect tool usage
• Add safeguards

Tasks
• Define at least two tools the agent can use
• Implement tool calling logic
• Demonstrate correct tool selection
• Show at least one failed or incorrect tool call
• Add safeguards against misuse or loops
Phase 6: Planning, Memory & Context
Coding: Required
Tools/Skills: Planning/task decomposition, conversation state, short-term/long-term
memory, memory reset/retention rules, multi-turn testing
• Introduce multi-step reasoning
• Add memory handling
• Improve multi-turn conversations

Tasks
Implement multi-step reasoning or planning logic
• Add short-term or long-term memory
• Define memory retention and reset behaviour
• Demonstrate improved conversation quality

Phase 7: Adaptive Behaviour
Coding: Required
Tools/Skills: Feedback collection, storing feedback, behaviour adjustment logic, before/after
comparisons, change explanation
• Introduce feedback signals
• Show behavioural change
• Explain the adaptation logic

Tasks
• Store feedback for future interactions
• Modify behaviour based on feedback
• Demonstrate before vs after behaviour
• Explain what changed and why
Phase 8: Deployment Readiness
Coding: Required
Tools/Skills: Packaging and reproducibility, environment management, basic deployment
(local/cloud), logging/tracing, latency/error capture, graceful failure handling
• Package for deployment
• Add logging and tracing
• Handle runtime failures

Tasks
• Deploy locally or on the cloud
• Capture latency and error logs
• Demonstrate graceful failure handling
• Document deployment assumptions and limitations

Phase 9: Evaluation & Engineering Review
Coding: Required
Tools/Skills: Test harness design, evaluation prompts, quality/consistency metrics, failure
analysis (root cause), safety/ethics review, improvement roadmap
• Measure response quality
• Analyze failures
• Review safety and ethics
Tasks
• Create evaluation prompts and test scenarios
• Measure quality and consistency metrics
• Perform root cause analysis
• Propose next-step improvements


Additional Project Review: Tools and Skills Given vs. Used

| Phase | Skills/tools mentioned in the spec | Actually used in the project | Status |
|---|---|---|---|
| Phase 1 | Problem framing, user persona, workflow mapping, requirements, success criteria, edge-case thinking | Problem framing, safety contract, requirements | Implemented |
| Phase 2 | Python, CLI, input/output handling, rules/templates, logging | Baseline Python agent, sample logs, limitations demonstrated | Implemented |
| Phase 3 | LLM integration, prompt engineering, prompt versioning, structured comparison | OpenAI LLM, prompt comparison, default prompt selected | Implemented |
| Phase 4 | Embeddings, semantic search, RAG, chunking, FAISS, vector store | FAISS vector store, embeddings, retrieval, RAG | Implemented |
| Phase 5 | Tool/function calling, schemas, routing logic, guardrails, loop prevention | calculator, loan_calculator, loan_process_lookup, atm_usage_lookup, transfer_limit_lookup, foreign_transfer_fee_lookup, policy_lookup, no-tool fallback, safeguards | Implemented |
| Phase 6 | Planning, memory, context, short-term/long-term memory, multi-turn testing | Limited session context available; not full persistent memory | Partial |
| Phase 7 | Feedback collection, adaptive behavior, before/after comparison | Response-specific feedback, reason/correction-guided retry, session-scoped style adaptation, minimized feedback log, and safety regression tests | Implemented (session-scoped; not model training) |
| Phase 8 | Packaging, deployment, logging, tracing, runtime failure handling | Streamlit app and basic logging exist; basic deployment readiness | Partial |
| Phase 9 | Evaluation prompts, metrics, root-cause analysis, safety and ethics review | Evaluation reports and tests exist | Implemented |

Summary:
• Given in the spec: 9 phases and more than 50 distinct skill/tool mentions across the workflow.
• Actually used in this project: the core AI agent stack, including Python, OpenAI/LLM, embeddings, FAISS, RAG, Streamlit, safety guardrails, and evaluation logging.
• Real tools implemented in Phase 5: calculator, loan_calculator, policy_lookup, loan_process_lookup, atm_usage_lookup, transfer_limit_lookup, foreign_transfer_fee_lookup, plus a safe no-tool fallback path.
• The project now covers more banking topic routing, including personal/home loan process queries, ATM usage, online transfer limits, and foreign transfer charges.
• Current limitation: the vectorstore rebuild is blocked when the OpenAI account has insufficient quota (`429 credit_balance_exhausted`), so embedding/index refresh requires billed API credits before future vector-store updates can complete.
• Not fully implemented: persistent long-term memory, cross-session feedback learning, and full production deployment packaging.

Overall, the project meets the main requirement of building a working banking support agent, and it now includes a broader Phase 5 tool layer than the original baseline. Feedback adaptation is limited to the current chat; long-term memory and cross-session learning remain out of scope.



