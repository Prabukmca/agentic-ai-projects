"""
Hierarchical Planning AI System using CrewAI
Builds a comprehensive event planning system with multiple agents working together
"""

import os
import json
from crewai import Agent, Task, Crew
from langchain.llms import OpenAI

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

llm = OpenAI(api_key=openai_api_key)


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

# 1. Planning Agent - Breaks down high-level goals into structured multi-level plans
planning_agent = Agent(
    role="Strategic Event Planner",
    goal="Break down high-level event goals into a comprehensive, structured multi-level plan with clear phases and deliverables",
    backstory="You are an expert event strategist with 15+ years of experience. You excel at analyzing event requirements and creating detailed hierarchical plans that cover all aspects from pre-event to post-event activities.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 2. Research Agent - Researches vendors, venues, and scheduling options
research_agent = Agent(
    role="Vendor & Venue Research Specialist",
    goal="Research and recommend optimal vendors, venues, and scheduling options based on event requirements",
    backstory="You are a meticulous researcher specializing in vendor evaluation and venue selection. You analyze options comprehensively, considering quality, cost, availability, and suitability for different event types.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 3. Budget Agent - Creates comprehensive event budgets
budget_agent = Agent(
    role="Event Budget Manager",
    goal="Build detailed, itemized budgets that cover all event expenses with contingency planning",
    backstory="You are a financial expert in event management. You create accurate, itemized budgets with realistic cost estimates, vendor quotes, and contingency buffers. You optimize spending while maintaining quality.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 4. Schedule Agent - Creates detailed event-day schedules
schedule_agent = Agent(
    role="Event Day Coordinator",
    goal="Create detailed, minute-by-minute event day schedules that ensure smooth flow and optimal guest experience",
    backstory="You are a logistics expert with extensive experience in event execution. You create detailed timelines considering setup, duration of activities, buffer times, and contingencies.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# 5. Coordinator Agent - Final consolidation and integration
coordinator_agent = Agent(
    role="Chief Event Coordinator",
    goal="Consolidate all planning elements into a comprehensive, integrated final event plan",
    backstory="You are the final authority on event planning. You review all components, ensure consistency, identify conflicts, and produce a final consolidated plan that all teams can execute.",
    verbose=True,
    allow_delegation=True,
    llm=llm
)


# ============================================================================
# TASK DEFINITIONS
# ============================================================================

def create_tasks(event_description):
    """
    Create a set of tasks based on the event description
    """
    
    # Task 1: Strategic Planning
    task_1_plan = Task(
        description=f"""
        Analyze this event requirement and create a comprehensive hierarchical plan:
        
        {event_description}
        
        Break it down into:
        1. Pre-Event Phase (planning, coordination)
        2. Setup Phase (vendor coordination, venue preparation)
        3. Event Phase (timeline and flow)
        4. Post-Event Phase (follow-up, feedback)
        
        For each phase, identify:
        - Key milestones
        - Responsible parties
        - Dependencies
        - Success criteria
        """,
        agent=planning_agent,
        expected_output="A structured 4-phase hierarchical event plan with milestones and deliverables"
    )
    
    # Task 2: Research & Recommendations
    task_2_research = Task(
        description=f"""
        Based on this event requirement, research and recommend:
        
        {event_description}
        
        Provide recommendations for:
        1. Venue options (3-5 options with pros/cons)
        2. Catering vendors (3-5 options with pricing)
        3. Audio/Visual services (2-3 providers)
        4. Timing & Scheduling constraints
        5. Seasonal/Weather considerations
        
        For each option, provide:
        - Brief description
        - Estimated cost range
        - Availability
        - Suitability rating
        - Key advantages/disadvantages
        """,
        agent=research_agent,
        expected_output="Detailed research summary with vendor recommendations and options"
    )
    
    # Task 3: Budget Creation
    task_3_budget = Task(
        description=f"""
        Create a comprehensive budget for:
        
        {event_description}
        
        Include itemized costs for:
        1. Venue rental
        2. Catering/Beverages
        3. Decoration/Ambiance
        4. Audio/Visual/Entertainment
        5. Staffing/Labor
        6. Transportation (if applicable)
        7. Permits/Insurance
        8. Contingency (10-15%)
        
        For each category:
        - List specific items
        - Quantity and unit cost
        - Total cost
        - Payment terms
        - Budget allocation percentage
        
        Provide a summary with:
        - Total estimated budget
        - Budget breakdown
        - Recommendations for cost optimization
        """,
        agent=budget_agent,
        expected_output="Detailed itemized budget with categories, costs, and optimization recommendations"
    )
    
    # Task 4: Event Day Schedule
    task_4_schedule = Task(
        description=f"""
        Create a detailed event-day schedule for:
        
        {event_description}
        
        Include:
        1. Setup timeline (hours before event)
        2. Guest arrival and check-in procedures
        3. Minute-by-minute event flow
        4. Meal service timing
        5. Key activities/entertainment
        6. Breaks and transitions
        7. Cleanup and venue restoration
        
        For each time block (15-30 min blocks):
        - Start and end time
        - Activity/description
        - Responsible party
        - Equipment/resources needed
        - Contingency plans
        
        Consider:
        - Guest experience flow
        - Staff coordination
        - Buffer times for transitions
        - Contingency timings
        """,
        agent=schedule_agent,
        expected_output="Detailed minute-by-minute event day schedule with activities and contingencies"
    )
    
    # Task 5: Final Consolidation
    task_5_consolidation = Task(
        description=f"""
        Review and consolidate all previous planning components into one comprehensive final event plan.
        
        Your consolidated plan should include:
        
        1. EXECUTIVE SUMMARY
           - Event overview
           - Goals and objectives
           - Expected outcomes
        
        2. HIERARCHICAL PLAN
           - 4-phase breakdown with milestones
        
        3. VENDOR & VENUE RECOMMENDATIONS
           - Selected vendors/venues with rationale
           - Backup options
        
        4. BUDGET SUMMARY
           - Total budget
           - Category breakdown
           - Payment schedule
        
        5. EVENT DAY MASTER SCHEDULE
           - Detailed timeline
           - Assignments
           - Contingency procedures
        
        6. RISK MITIGATION
           - Potential issues and solutions
           - Backup plans
           - Emergency contacts
        
        7. SUCCESS METRICS
           - How to measure event success
           - Follow-up procedures
        
        Ensure all components are consistent, dependencies are clear, and the plan is actionable.
        """,
        agent=coordinator_agent,
        expected_output="Comprehensive consolidated final event plan with all components integrated"
    )
    
    return [task_1_plan, task_2_research, task_3_budget, task_4_schedule, task_5_consolidation]


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_event_planning_system(event_description):
    """
    Execute the hierarchical planning system for a given event
    """
    
    print("\n" + "="*80)
    print("HIERARCHICAL EVENT PLANNING SYSTEM - CrewAI")
    print("="*80)
    print(f"\nEvent Description:\n{event_description}\n")
    print("="*80)
    print("Initializing planning crew...\n")
    
    # Create tasks
    tasks = create_tasks(event_description)
    
    # Create crew with agents and tasks
    crew = Crew(
        agents=[
            planning_agent,
            research_agent,
            budget_agent,
            schedule_agent,
            coordinator_agent
        ],
        tasks=tasks,
        verbose=True
    )
    
    # Execute the crew
    print("\nStarting hierarchical planning process...\n")
    result = crew.kickoff()
    
    return result


# ============================================================================
# EXAMPLE EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Example event description
    example_event = """
    Event Type: Corporate Team Building Event
    Date: August 15, 2026
    Location: San Francisco Bay Area
    Expected Attendees: 150 employees + 20 partners
    Duration: Full day (8 AM - 6 PM)
    Budget Range: $25,000 - $40,000
    
    Requirements:
    - Mix of indoor and outdoor activities
    - Catering for breakfast, lunch, and afternoon snacks
    - Team competitions and building exercises
    - Networking opportunities
    - Professional AV setup for opening/closing remarks
    - COVID-safe indoor ventilation standards
    - Wheelchair accessible venue
    - Transportation from downtown SF offices
    """
    
    # Run the planning system
    final_plan = run_event_planning_system(example_event)
    
    # Output results
    print("\n" + "="*80)
    print("FINAL CONSOLIDATED EVENT PLAN")
    print("="*80)
    print(final_plan)
    
    # Save results to file
    output_file = "event_plan_output.txt"
    with open(output_file, "w") as f:
        f.write("HIERARCHICAL EVENT PLANNING SYSTEM - FINAL OUTPUT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Event Description:\n{example_event}\n\n")
        f.write("="*80 + "\n")
        f.write("FINAL CONSOLIDATED PLAN\n")
        f.write("="*80 + "\n\n")
        f.write(str(final_plan))
    
    print(f"\n\nPlan saved to: {output_file}")
