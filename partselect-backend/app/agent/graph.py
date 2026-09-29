

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import AgentNodes
from typing import Dict


def should_search(state: AgentState) -> str:
    """
    Decision: Should we search for products?
    
    Returns: "search" or "respond"
    """
    intent = state.get("intent")
    
    search_intents = [
        "search_part",
        "diagnose_issue", 
        "installation_help",
        "compatibility_check",
        "product_details"
    ]
    
    if intent in search_intents:
        return "search"
    else:
        return "respond"


def should_gather_context(state: AgentState) -> str:
    """
    Decision: Do we need more context from ChromaDB?
    
    Returns: "gather_context" or "recommend"
    """
    intent = state.get("intent")
    search_results = state.get("search_results", [])
    
    # If we have results and intent needs context, gather it
    if search_results and intent in ["diagnose_issue", "installation_help"]:
        return "gather_context"
    elif search_results:
        return "recommend"
    else:
        return "respond"


def create_agent_graph() -> StateGraph:
    """
    Create the agent graph
    
    Flow:
    1. Understand query (always)
    2. Search products (if needed)
    3. Gather context (if needed)
    4. Recommend parts (if we have results)
    5. Generate response (always)
    """
    
    # Initialize nodes
    nodes = AgentNodes()
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("understand", nodes.understand_query)
    workflow.add_node("search", nodes.search_products)
    workflow.add_node("gather_context", nodes.gather_context)
    workflow.add_node("recommend", nodes.recommend_parts)
    workflow.add_node("respond", nodes.generate_response)
    
    # Set entry point
    workflow.set_entry_point("understand")
    
    # Add edges
    workflow.add_conditional_edges(
        "understand",
        should_search,
        {
            "search": "search",
            "respond": "respond"
        }
    )
    
    workflow.add_conditional_edges(
        "search",
        should_gather_context,
        {
            "gather_context": "gather_context",
            "recommend": "recommend",
            "respond": "respond"
        }
    )
    
    workflow.add_edge("gather_context", "recommend")
    workflow.add_edge("recommend", "respond")
    workflow.add_edge("respond", END)
    
    # Compile graph
    return workflow.compile()


# Global agent instance
_agent_graph = None


def get_agent():
    """Get or create agent graph"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph