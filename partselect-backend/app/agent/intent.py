# """
# Intent Classification
# """

# import re
# from typing import Tuple, List, Optional
# from app.core.llm import get_llm_client
# import json


# class IntentClassifier:
#     """Classify user intent and extract entities"""
    
#     # Intent patterns
#     SEARCH_PATTERNS = [
#         r"(?:find|search|looking for|need|show me|where can i (?:find|get|buy))\s+(?:a\s+|an\s+|the\s+)?(.+)",
#         r"do you (?:have|sell|carry)\s+(?:a\s+|an\s+|the\s+)?(.+)",
#     ]
    
#     PRODUCT_DETAIL_PATTERNS = [
#         r"(?:tell me|what|details?)\s+(?:about|on)\s+(?:part\s+)?([A-Z]{2}\d{7,8})",
#         r"(?:information|info|details?)\s+(?:for|on|about)\s+(?:part\s+)?([A-Z]{2}\d{7,8})",
#         r"what'?s?\s+(?:included|in)\s+(?:with\s+)?(?:part\s+)?([A-Z]{2}\d{7,8})",
#     ]
    
#     DIAGNOSIS_PATTERNS = [
#         r"(?:my|the|our)\s+([\w\s]+?)\s+stopped\s+(.+)",
#         r"(?:my|the|our)\s+([\w\s]+?)\s+(?:is|isn't|won't|not|doesn't)\s+(.+)",
#         r"(.+)\s+(?:not working|broken|won't work|doesn't work|stopped working|quit working)",
#         r"(.+)\s+(?:is|are)\s+(?:broken|leaking|noisy|loud|making noise)",
#         r"(?:problem|issue|trouble)\s+with\s+(.+)",
#         r"why (?:is|isn't|won't|doesn't)\s+(?:my|the)\s+(.+)",
#     ]
    
#     INSTALLATION_PATTERNS = [
#     # Direct installation requests
#     r"how (?:do i|to|can i)\s+(?:install|replace|fix|change|remove)\s+(?:a\s+|an\s+|the\s+)?(.+)",
#     r"installation (?:for|of|help|instructions)\s+(?:for\s+)?(?:a\s+|an\s+|the\s+)?(.+)",
#     r"(?:can you|help me|show me how to)\s+(?:install|replace|change)\s+(?:a\s+|an\s+|the\s+)?(.+)",
    
#     # VIDEO-specific patterns (NEW)
#     r"(?:do you have|is there|show me|find|where)\s+(?:a\s+|an\s+)?(?:installation\s+)?(?:video|tutorial|guide)\s+(?:for|on|about)\s+(.+)",
#     r"video\s+(?:tutorial|guide|instructions?)?\s+(?:for|on|to)\s+(?:install|replace)\s+(.+)",
#     r"(?:installation|replace|repair)\s+(?:video|tutorial)\s+(.+)",
    
#     # Part number + video
#     r"(?:video|tutorial|instructions?|guide)\s+(?:for|on)?\s+(?:part\s+)?([A-Z]{2}\d{7,8})",
# ]
    
#     COMPATIBILITY_PATTERNS = [
#         r"(?:will|does|can)\s+(.+)\s+(?:work with|fit|compatible|work on)",
#         r"(?:is|are)\s+(?:this|the|a)\s+(.+?)\s+compatible",
#         r"compatible with",
#         r"fit (?:my|the|a)",
#     ]
    
#     def __init__(self):
#         self.llm = get_llm_client()
    
#     def extract_part_number(self, query: str) -> Optional[str]:
#         """Extract part number (PS followed by 7-8 digits)"""
#         import re
#         pattern = r"\b(PS\d{7,8})\b"
#         match = re.search(pattern, query, re.IGNORECASE)
#         if match:
#             part = match.group(1).upper()
#             return part
#         return None
    
#     def extract_model_number(self, query: str) -> Optional[str]:
#         """
#         Extract model number
#         Rule: Any alphanumeric code that doesn't start with PS
#         """
#         import re
        
#         # FIXED PATTERN: Allow multiple letters/digits at end
#         # Examples: WRS325SDHZ, WDT780SAEM1, WDT750SAHZ0
#         pattern = r"\b([A-Z]{2,4}\d{3,}[A-Z0-9]*)\b"
        
#         all_codes = re.findall(pattern, query, re.IGNORECASE)
        
#         print(f"[Intent] All codes found: {all_codes}")
        
#         for code in all_codes:
#             code_upper = code.upper()
            
#             # Skip part numbers (start with PS)
#             if code_upper.startswith('PS'):
#                 print(f"[Intent] Skipping {code_upper} (part number)")
#                 continue
            
#             # This is the model number
#             print(f"[Intent] Found model: {code_upper}")
#             return code_upper
        
#         return None
    
#     def clean_extracted_text(self, text: str) -> str:
#         """Remove articles and clean up extracted text"""
#         import re
#         text = re.sub(r"^(a|an|the)\s+", "", text, flags=re.IGNORECASE)
#         return text.strip()
    
#     async def classify_async(self, query: str, context: Optional[dict] = None) -> Tuple[str, dict]:
#         """Async classification"""
#         query_lower = query.lower()
        
#         # Extract part number and model number
#         part_number = self.extract_part_number(query)
#         model_number = self.extract_model_number(query)
        
#         print(f"[Intent] Query: '{query}'")
#         print(f"[Intent] Extracted - Part: {part_number}, Model: {model_number}")
        
#         # Check for product detail request
#         if part_number:
#             for pattern in self.PRODUCT_DETAIL_PATTERNS:
#                 match = re.search(pattern, query, re.IGNORECASE)
#                 if match:
#                     return "product_details", {
#                         "part_number": part_number,
#                         "query": part_number,
#                         "method": "pattern"
#                     }
        
#         # Check diagnosis
#         for pattern in self.DIAGNOSIS_PATTERNS:
#             match = re.search(pattern, query_lower)
#             if match:
#                 appliance = match.group(1).strip() if match.lastindex >= 1 else None
#                 symptom = match.group(2).strip() if match.lastindex >= 2 else match.group(1).strip()
                
#                 return "diagnose_issue", {
#                     "appliance": appliance,
#                     "symptom": symptom,
#                     "method": "pattern"
#                 }
        
#         # Check search
#         for pattern in self.SEARCH_PATTERNS:
#             match = re.search(pattern, query_lower)
#             if match:
#                 extracted = self.clean_extracted_text(match.group(1))
                
#                 return "search_part", {
#                     "query": extracted,
#                     "part_number": part_number,
#                     "method": "pattern"
#                 }
        
#         # Check installation
#         for pattern in self.INSTALLATION_PATTERNS:
#             match = re.search(pattern, query_lower)
#             if match:
#                 extracted = self.clean_extracted_text(match.group(1))
                
#                 return "installation_help", {
#                     "part": extracted,
#                     "part_number": part_number,
#                     "query": extracted,
#                     "method": "pattern"
#                 }
        
#         # Check compatibility
#         for pattern in self.COMPATIBILITY_PATTERNS:
#             if re.search(pattern, query_lower):
#                 print(f"[Intent] Matched COMPATIBILITY")
                
#                 # Build entities
#                 entities = {
#                     "method": "pattern",
#                     "part_number": part_number,
#                     "model_number": model_number,
#                 }
                
#                 # Try to extract part description
#                 if "water filter" in query_lower:
#                     entities["query"] = "water filter"
#                 elif "ice maker" in query_lower:
#                     entities["query"] = "ice maker"
#                 elif part_number:
#                     entities["query"] = part_number
#                 else:
#                     entities["query"] = query
                
#                 print(f"[Intent] Compatibility entities: {entities}")
                
#                 return "compatibility_check", entities
        
#         # Fallback to LLM
#         return await self._classify_with_llm_async(query, context)
    
#     async def _classify_with_llm_async(self, query: str, context: Optional[dict]) -> Tuple[str, dict]:
#         """Async LLM classification"""
#         # ... existing LLM code ...
#         return "general_question", {"query": query, "method": "llm_fallback"}
    
#     def extract_symptoms(self, query: str) -> List[str]:
#         """Extract symptoms from query"""
#         symptom_keywords = [
#             "not working", "broken", "leaking", "noisy", "not cleaning",
#             "not dispensing", "not making", "won't turn on", "won't start",
#             "too cold", "too warm", "frost", "ice buildup", "smells",
#             "not draining", "not filling", "not spinning", "stopped"
#         ]
        
#         symptoms = []
#         query_lower = query.lower()
        
#         for keyword in symptom_keywords:
#             if keyword in query_lower:
#                 symptoms.append(keyword)
        
#         return symptoms
"""
Intent Classification using LLM
"""

import json
from typing import Tuple, Dict, Optional
from app.core.llm import get_llm_client


class IntentClassifier:
    """Classify user intent using LLM"""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    async def classify_async(self, query: str, context: Optional[dict] = None) -> Tuple[str, dict]:
        """
        Classify intent using LLM with conversation context
        """
        
        # Enhanced system prompt with conversation awareness
        system_prompt = """You are an intent classification system for an appliance parts assistant.

IMPORTANT: Consider the conversation context. If the assistant previously asked for information (like a model number), and the user provides it, classify appropriately.

Classify the user's query into ONE of these intents:

1. **search_part** - User wants to find/buy a specific part or browse options
   Examples: 
   - "I need a water filter"
   - "show me ice makers"
   - "find ice maker options"
   - "what ice makers do you have?"
   - "I'm looking for ice maker parts"
   
2. **diagnose_issue** - User describes a problem/symptom
   Examples: 
   - "my ice maker stopped working"
   - "dishwasher is leaking"
   
3. **installation_help** - User needs installation guidance with specific part number
   Examples: 
   - "how do I install part PS11701542?"
   - "installation video for PS11759673"
   
4. **compatibility_check** - User checking part compatibility
   Examples: 
   - "will PS11701542 fit my WRS325SDHZ?"
   
5. **product_details** - User wants info about ONE specific part (with part number)
   Examples: 
   - "tell me about PS11701542"
   - "what's included with PS11759673?"
   
6. **general_question** - General questions, asking for recommendations without specifics
   Examples: 
   - "what causes ice maker problems?"
   - "how do I install a water filter?" (no part number)
   - "how much does an ice maker cost?"

KEY DISTINCTIONS:
- "show me ice makers" / "I need ice maker options" → search_part (browsing/shopping)
- "tell me about PS11701542" → product_details (specific part info)
- "how to install ice maker" (no part #) → general_question
- "how to install PS11701542" → installation_help

Extract entities:
- part_number: PS + 7-8 digits
- model_number: Appliance model 
- appliance_type: refrigerator, dishwasher, etc.
- brand: Samsung, Whirlpool, etc.
- symptom: Full symptom description
- search_query: Cleaned search term (remove filler words like "show me", "different", "options")
CRITICAL: Distinguishing Part Numbers from Model Numbers

**Part Numbers:**
- Always start with "PS" 
- Start with "W" followed by 8 digits (e.g., W10291030)
- Start with "AP" (e.g., AP5982535)

**Model Numbers:**
- Alphanumeric codes that are NOT part numbers
- Examples: 
  - WRS325SDHZ (3 letters + digits + letters)
  - D7824706Q (1 letter + digits + letter)
  - WDT780SAEM1 (3 letters + digits + letters + digit)
  - ED2KHAXVQ (2 letters + digits + letters)

**Decision Rules:**

1. If it's an alphanumeric code that's NOT a part number → it's a MODEL number
2. When user says "is it compatible with/ to XYZ":
   -  XYZ is a model number

CLEANING RULES for search_query:
- "show me different ice maker options" → "ice maker"
- "I need water filter options" → "water filter"
- "find me spray arms" → "spray arm"
- Remove: "show me", "different", "options", "I need", "find me", "looking for"

Respond ONLY with valid JSON:
{
  "intent": "search_part",
  "entities": {
    "appliance_type": "refrigerator",
    "search_query": "ice maker"
  },
  "confidence": 0.95,
  "reasoning": "User wants to browse ice maker options"
}"""
        # Build user prompt with context
        user_prompt = f"Classify this query: \"{query}\""
        
        if context:
            user_prompt += f"\n\nConversation context:"
            
            if context.get("waiting_for"):
                user_prompt += f"\n- Assistant is waiting for: {context['waiting_for']}"
            
            if context.get("appliance_type"):
                user_prompt += f"\n- Known appliance: {context['appliance_type']}"
            
            if context.get("conversation_history"):
                recent = context["conversation_history"][-3:]  # Last 3 queries
                user_prompt += f"\n- Previous queries: {', '.join(recent)}"
            
            if context.get("last_intent"):
                user_prompt += f"\n- Previous intent: {context['last_intent']}"
        
        # Call LLM
        try:
            response = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            
            intent = result.get("intent", "general_question")
            entities = result.get("entities", {})
            entities["confidence"] = result.get("confidence", 0.7)
            entities["method"] = "llm"
            
            print(f"[Intent] Classified as: {intent}")
            print(f"[Intent] Entities: {entities}")
            
            return intent, entities
            
        except Exception as e:
            print(f"[Intent] Error: {e}")
            return "general_question", {"query": query, "method": "error_fallback"}
    def extract_model_or_part(self, query: str) -> Dict[str, Optional[str]]:
        """
        Extract and distinguish between part numbers and model numbers
        
        If TWO codes are found, determine which is part and which is model
        """
        import re
        
        result = {"part_number": None, "model_number": None}
        
        # Find all alphanumeric codes
        codes = re.findall(r"\b([A-Z0-9]{6,15})\b", query, re.IGNORECASE)
        
        print(f"[Intent] Found {len(codes)} codes: {codes}")
        
        part_candidates = []
        model_candidates = []
        
        for code in codes:
            code_upper = code.upper()
            
            # Classify as part or model
            if code_upper.startswith('PS'):
                part_candidates.append(code_upper)
            elif re.match(r"^W\d{8}$", code_upper):
                part_candidates.append(code_upper)
            elif code_upper.startswith('AP'):
                part_candidates.append(code_upper)
            else:
                model_candidates.append(code_upper)
        
        # Assign results
        if part_candidates:
            result["part_number"] = part_candidates[0]
            print(f"[Intent] Part number: {result['part_number']}")
        
        if model_candidates:
            result["model_number"] = model_candidates[0]
            print(f"[Intent] Model number: {result['model_number']}")
        
        return result
    def extract_symptoms(self, query: str) -> list:
       
        return []