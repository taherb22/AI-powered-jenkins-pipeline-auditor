
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .agents import lead_auditor, worker_auditor, enhancer_auditor,holistic_auditor



def reviewer_node(state: AgentState) -> str:
    """
    This is the simplest form of a reviewer. It acts as a gatekeeper.
    Its only job in this first iteration is to check if the specialists are done.
    """
    print("--- Reviewer: Checking workflow status... ---")
    print("--- Reviewer: All specialist tasks complete. Proceeding to enhancer. ---")
    return "finish"



def build_graph() -> StateGraph:
    """
    Builds the LangGraph StateGraph that defines the multi-agent workflow.
    """
    print("--- Building the agent workflow graph... ---")
    
    builder = StateGraph(AgentState)

   
    builder.add_node("planner", lead_auditor.plan_initial_audit)
    builder.add_node("holistic_auditor", holistic_auditor.run_holistic_audit) 
    builder.add_node("specialists", worker_auditor.run_specialist_audit)
    
    builder.add_node("enhancer", enhancer_auditor.generate_final_report)
    builder.add_node("save_report", enhancer_auditor.save_report_to_file)
  
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "holistic_auditor")
    builder.add_edge("holistic_auditor", "specialists")
    
    builder.add_conditional_edges(
        "specialists",
        reviewer_node,
        {
            "finish": "enhancer"
        }
    )

    
    builder.add_edge("enhancer", "save_report")
    builder.add_edge("save_report", END)
    print("--- Graph build complete. Compiling... ---")
    return builder.compile()


app_workflow = build_graph()
print("--- Application workflow is compiled and ready. ---")