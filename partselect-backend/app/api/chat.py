"""
Chat API endpoint
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
import json
import redis
from datetime import timedelta
from decimal import Decimal

from app.agent.graph import get_agent

# Define router
router = APIRouter()

# Custom JSON encoder for Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float"""
    if isinstance(obj, dict):
        return {k: convert_decimals_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

# Initialize Redis
try:
    redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    redis_client.ping()
    print("[Redis] Connected successfully")
except Exception as e:
    print(f"[Redis] Connection failed: {e}")
    redis_client = None


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    conversation_id: str
    intent: str
    recommended_parts: List[Dict]
    metadata: Dict


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with state persistence"""
    
    user_message = request.message
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    print(f"\n{'='*70}")
    print(f"[Chat] Message: {user_message}")
    print(f"[Chat] Conversation ID: {conversation_id}")
    
    # Initialize default state
    default_state = {
        "messages": [],
        "conversation_history": [],
        "user_query": "",
        "appliance_type": None,
        "brand": None,
        "model_number": None,
        "part_number": None,
        "symptom": None,
        "waiting_for": None,
        "search_query": None,
        "search_results": [],
        "relevant_docs": [],
        "recommended_parts": [],
        "intent": "",
        "confidence": 0.0,
        "reasoning": "",
        "symptoms": []
    }
    
    # LOAD PREVIOUS STATE FROM REDIS
    state = default_state.copy()
    
    if redis_client:
        state_key = f"conversation:{conversation_id}"
        
        try:
            previous_state = redis_client.get(state_key)
            
            if previous_state:
                loaded_state = json.loads(previous_state)
                state.update(loaded_state)
                print(f"[Chat] Loaded state - appliance: {state.get('appliance_type')}, brand: {state.get('brand')}, model: {state.get('model_number')}, part: {state.get('part_number')}")
            else:
                print("[Chat] No previous state, using defaults")
                
        except Exception as e:
            print(f"[Chat] Error loading state: {e}")
    else:
        print("[Chat] Redis not available, state won't persist")
    
    # Add current user message
    state["user_query"] = user_message
    state["messages"].append({
        "role": "user",
        "content": user_message
    })
    
    try:
        # Run agent
        agent = get_agent()
        final_state = await agent.ainvoke(state)
        
        # Extract response
        assistant_messages = [
            msg for msg in final_state.get("messages", []) 
            if msg.get("role") == "assistant"
        ]
        
        response_message = assistant_messages[-1]["content"] if assistant_messages else "I'm here to help! How can I assist you?"
        
        # SAVE UPDATED STATE TO REDIS
        if redis_client:
            try:
                # Convert Decimals to float
                serializable_state = convert_decimals_to_float(final_state)
                
                redis_client.setex(
                    state_key,
                    timedelta(hours=24),
                    json.dumps(serializable_state, cls=DecimalEncoder)
                )
                print(f"[Chat] Saved state to Redis (expires in 24h)")
                print(f"[Chat] State summary - part: {serializable_state.get('part_number')}, model: {serializable_state.get('model_number')}, brand: {serializable_state.get('brand')}")
            except Exception as e:
                print(f"[Chat] Error saving state: {e}")
                import traceback
                traceback.print_exc()
        
        # Prepare response
        response = ChatResponse(
            message=response_message,
            conversation_id=conversation_id,
            intent=final_state.get("intent", "general_question"),
            recommended_parts=final_state.get("recommended_parts", []),
            metadata={
                "confidence": final_state.get("confidence", 0.0),
                "appliance_type": final_state.get("appliance_type"),
                "brand": final_state.get("brand"),
                "model_number": final_state.get("model_number"),
                "symptoms": final_state.get("symptoms", [])
            }
        )
        
        print(f"[Chat] Response generated successfully")
        print(f"{'='*70}\n")
        
        return response
        
    except Exception as e:
        print(f"[Chat] Error: {e}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )