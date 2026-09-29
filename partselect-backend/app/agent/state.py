

from typing import TypedDict, List, Dict, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    State that flows through the agent graph
    
    Why TypedDict? LangGraph needs type hints for state management
    """
    
    # Conversation basics
    messages: Annotated[List[Dict], operator.add]  # Chat history
    user_query: str  # Current user message
    conversation_history: List[str]  # Previous user queries
    waiting_for: Optional[str]  
    # User context
    appliance_type: Optional[str]  # "refrigerator" or "dishwasher"
    symptoms: List[str]  # What's broken?
    model_number: Optional[str]
    part_number: Optional[str]
    
    # Search results
    search_results: List[Dict]  # Products from search
    relevant_docs: List[Dict]  # ChromaDB semantic search results
    
    # Agent reasoning
    intent: Optional[str]  # "search_part", "diagnose_issue", "installation_help"
    confidence: float  # How confident is the agent?
    next_action: Optional[str]  # What should agent do next?
    search_query: Optional[str]
    # Recommendations
    recommended_parts: List[Dict]  # Parts to suggest
    reasoning: str  # Why these parts?
    
    # Metadata
    conversation_id: str
    created_at: datetime
    turn_count: int


class ConversationContext:
    """
    Helper class to manage conversation context

    """
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.appliance_type: Optional[str] = None
        self.model_number: Optional[str] = None
        self.symptoms: List[str] = []
        self.discussed_parts: List[str] = []  # Track what we've talked about
        
    def update_from_state(self, state: AgentState):
        """Extract persistent context from state"""
        if state.get("appliance_type"):
            self.appliance_type = state["appliance_type"]
        if state.get("model_number"):
            self.model_number = state["model_number"]
        if state.get("symptoms"):
            self.symptoms.extend(state["symptoms"])
            self.symptoms = list(set(self.symptoms))  # Deduplicate
    
    def to_dict(self) -> Dict:
        """Serialize for database storage"""
        return {
            "conversation_id": self.conversation_id,
            "appliance_type": self.appliance_type,
            "model_number": self.model_number,
            "symptoms": self.symptoms,
            "discussed_parts": self.discussed_parts
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationContext":
        """Deserialize from database"""
        ctx = cls(data["conversation_id"])
        ctx.appliance_type = data.get("appliance_type")
        ctx.model_number = data.get("model_number")
        ctx.symptoms = data.get("symptoms", [])
        ctx.discussed_parts = data.get("discussed_parts", [])
        return ctx