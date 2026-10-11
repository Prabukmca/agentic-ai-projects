

Instructions
Problem Statement

Your goal is to build a Hierarchical Planning AI System using CrewAI that:

Breaks down the high-level event goal into a structured multi-level plan.
Researches vendors, venues, and scheduling options.
Builds a complete event budget.
Creates a full event-day schedule.
Produces a final consolidated event plan.
You are not expected to integrate real APIs or build a UI. Focus on clear planning logic, readable text outputs, and a crew of agents that work together in a sensible sequence.

Required System Components

You must design and implement the following CrewAI agents:

Event Planner Agent (Hierarchical Planner)

Breaks the big goal into pillars: venue, logistics, speakers, vendors, schedule, budget.
Generates sub-tasks and success metrics for each pillar.
Produces a hierarchical plan (Level 1 → Level 2 → Level 3).
Vendor Research Agent

Research for:
Catering vendors (2–3 options).
Audio/visual vendors.
Seating & event décor providers.
Optional: Stage setup companies.
Budget Analyst Agent

Builds detailed cost estimates.
Breaks down by category (venue, F&B, décor, A/V, labour, marketing).
Suggests cost-saving strategies.
Outputs total budget estimate & “must-book-first” items.
Schedule Designer Agent

Creates a full-day event schedule.
Includes keynote sessions, buffer times, breaks, workshops, and networking blocks.
Includes speaker preparation windows.
Should be realistic and time-bound.
Final Event Coordinator Agent

Consolidates all outputs into one structured event plan.
Includes booking checklist, timeline, risks, and contingencies.
Produces a final formatted deliverable.
Required Dynamic Inputs

Your CrewAI tasks must use placeholders:

{event_goal} → e.g., “Plan a 1-day corporate innovation summit”.
{date} → e.g., “2025-11-15”.
{attendee_count} → e.g., “300 attendees”.
{preferences} → e.g., “Premium look, vegetarian food options, mid-range budget”.
These must flow through multiple tasks, so that later agents (for example, Budget Analyst or Schedule Designer) can also “see” the event goal, date, attendee count, and preferences.

Assignment Tasks

You must implement the following in Python using CrewAI:

Task A — Build all 5 agents

Define the five agents listed under “Required System Components”.
Each must have:
Role
Goal
Backstory
LLM instance
Task B — Create 5 Tasks

Define one CrewAI Task for each agent.
Use structured description & expected_output.
Inject dynamic placeholders correctly.
Task C — Build the Crew

Define list of agents.
Define list of tasks.
Task D — Run the System

Pass dynamic inputs using:

crew.kickoff({"event_goal": ..., "date": ..., "attendee_count": ..., "preferences": ...})


Print final consolidated output.
 

Expected Output
Your final output should include:

Hierarchical Event Plan.
Vendor Research Summary.
Budget Table + Total Estimated Cost.
Full-Day Schedule.
Consolidated Final Event Plan.
 

Example Dynamic Input for Testing
Here are sample inputs you can use:

sample_inputs = {
    "event_goal": "Organize a 1-day corporate innovation summit focusing on AI and automation.",
    "date": "2025-11-15",
    "attendee_count": "300 attendees",
    "preferences": "Premium decor, vegetarian+vegan meal options, mid-range budget, interactive sessions"
}
Outcome for the Learner
By completing this assignment, you will deepen your understanding of:

Hierarchical planning.
Multi-agent CrewAI orchestration.
Dynamic task prompting.
Planning → Research → Budgeting → Scheduling → Synthesis workflows.
Exactly how to structure planning systems that move towards production-grade use cases.
 

How to Approach the Project
Start by restating the event goal in your own words using the dynamic inputs, then focus on getting the five agents and their tasks defined in a simple, readable way. Keep each agent tightly scoped to its role, and let the Event Planner Agent drive the structure that the others follow. Use plain, well-commented Python and do not worry about perfect prompts or real-world pricing – the priority is to see the hierarchical plan, vendor research, budget, schedule, and final plan all flow through one CrewAI pipeline.

 

Evaluation Checklist
All five agents are implemented with Role, Goal, Backstory, and LLM instance.
Each agent has a corresponding Task with structured description and expected_output.
Dynamic placeholders ({event_goal}, {date}, {attendee_count}, {preferences}) are correctly injected and passed through multiple tasks.
The crew runs end-to-end with crew.kickoff(...) and produces the expected sections in the output.
The hierarchical event plan, vendor summary, budget, schedule, and final plan are all present and coherent.