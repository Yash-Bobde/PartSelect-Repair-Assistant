


from typing import List, Dict, Optional
from app.agent.state import AgentState
from app.agent.tools import SearchTools
from app.agent.intent import IntentClassifier
from app.core.llm import get_llm_client
import json

import re

class AgentNodes:
    """
    Collection of node functions for the agent graph
    
    Each node:
    - Takes AgentState as input
    - Performs some action
    - Returns updated AgentState
    """
    
    def __init__(self):
        self.tools = SearchTools()
        self.intent_classifier = IntentClassifier()
        self.llm = get_llm_client()
    
    async def understand_query(self, state: AgentState) -> AgentState:
        """Node 1: Understand query and merge with existing context"""
        
        user_query = state["user_query"]
        
        # Build context from EXISTING state
        context = {
            "conversation_history": state.get("conversation_history", []),
            "waiting_for": state.get("waiting_for"),
            "appliance_type": state.get("appliance_type"),
            "brand": state.get("brand"),
            "model_number": state.get("model_number"),
            "part_number": state.get("part_number"),
            "symptom": state.get("symptom"),
            "last_intent": state.get("intent"),
        }
        
        print(f"[Agent] Existing context: {context}")
        
        # Classify new query
        intent, entities = await self.intent_classifier.classify_async(user_query, context)
        
        # Update intent (always update)
        state["intent"] = intent
        state["confidence"] = entities.get("confidence", 0.7)
        
        # ONLY update entities if they have NEW values
        for key, value in entities.items():
            if key in ["confidence", "method", "is_followup"]:
                continue
            
            if value:  # New value provided
                existing = state.get(key)
                
                if not existing:
                    # No existing value, set new one
                    state[key] = value
                    print(f"[Agent] Set {key} = {value}")
                elif existing != value:
                    # Different value, update it
                    state[key] = value
                    print(f"[Agent] Updated {key}: {existing} → {value}")
                else:
                    # Same value, keep it
                    print(f"[Agent] Kept {key} = {value}")
        
        # Update conversation history
        if "conversation_history" not in state:
            state["conversation_history"] = []
        state["conversation_history"].append(user_query)
        
        print(f"[Agent] Final state: appliance={state.get('appliance_type')}, brand={state.get('brand')}, model={state.get('model_number')}")
        
        return state
    
    async def search_products(self, state: AgentState) -> AgentState:
        """Node 2: Search for relevant products"""
        
        intent = state["intent"]
        query = state.get("search_query", state["user_query"])
        category = state.get("appliance_type")
        part_number = state.get("part_number")
        brand = state.get("brand")
        symptom = state.get("symptom")
        model_number = state.get("model_number")
        
        print(f"[Search] Intent: {intent}")
        print(f"[Search] Query: '{query}'")
        print(f"[Search] Category: {category}")
        print(f"[Search] Brand: {brand}")
        print(f"[Search] Symptom: {symptom}")
        
        search_results = []
        
        # PRIORITY 1: If we have a part number, get it directly
        if part_number:
            print(f"[Search] Searching by part number: {part_number}")
            product = await self.tools.get_product_details(part_number)
            if product:
                search_results = [product]
                print(f"[Search] Found product by part number")
        
        # PRIORITY 2: Search based on intent
        if not search_results:
            
            # COMPATIBILITY CHECK
            if intent == "compatibility_check":
                if part_number:
                    # Already got it above
                    pass
                elif model_number and not part_number:
                    # User provided only model, no part yet
                    print(f"[Search] Have model {model_number} but no part specified")
                else:
                    # Try searching by query
                    search_results = await self.tools.search_products_by_keyword(
                        keyword=query,
                        category=category,
                        limit=5
                    )
                    print(f"[Search] Compatibility search found {len(search_results)} results")
            
            # DIAGNOSIS - SEARCH BY SYMPTOM
            elif intent == "diagnose_issue":
                print(f"[Search] Diagnosis search...")
                
                # Build search terms from symptom and appliance
                search_terms = []
                
                if symptom:
                    symptom_clean = symptom.lower()
                    
                    # Extract key terms from symptom
                    if "ice maker" in symptom_clean or "ice" in symptom_clean:
                        search_terms.append("ice maker")
                        search_terms.append("ice maker assembly")
                    
                    if "water" in symptom_clean and "leak" in symptom_clean:
                        search_terms.append("water valve")
                        search_terms.append("water line")
                    
                    if "not making ice" in symptom_clean or "stopped making ice" in symptom_clean:
                        search_terms.append("ice maker assembly")
                        search_terms.append("ice maker")
                    
                    if "not working" in symptom_clean:
                        if category == "refrigerator":
                            search_terms.append("ice maker")
                        elif category == "dishwasher":
                            search_terms.append("control board")
                    
                    if "not cleaning" in symptom_clean:
                        search_terms.append("spray arm")
                        search_terms.append("wash pump")
                    
                    if "not draining" in symptom_clean:
                        search_terms.append("drain pump")
                    
                    if "leaking" in symptom_clean or "leak" in symptom_clean:
                        search_terms.append("gasket")
                        search_terms.append("seal")
                        search_terms.append("valve")
                    
                    if "noisy" in symptom_clean or "noise" in symptom_clean:
                        search_terms.append("motor")
                        search_terms.append("fan")
                
                # If no specific terms, use general terms based on appliance
                if not search_terms:
                    if category == "refrigerator":
                        search_terms = ["ice maker", "water filter", "thermostat"]
                    elif category == "dishwasher":
                        search_terms = ["spray arm", "pump", "valve"]
                    else:
                        # Fallback to query
                        search_terms = [query] if query else []
                
                print(f"[Search] Search terms for diagnosis: {search_terms}")
                
                # Search for each term
                for term in search_terms[:3]:  # Limit to 3 searches
                    results = await self.tools.search_products_by_keyword(
                        keyword=term,
                        category=category,
                        limit=5
                    )
                    search_results.extend(results)
                    print(f"[Search] Found {len(results)} results for '{term}'")
                
                # Deduplicate
                seen = set()
                unique_results = []
                for result in search_results:
                    if result['part_number'] not in seen:
                        seen.add(result['part_number'])
                        unique_results.append(result)
                
                search_results = unique_results[:10]
                print(f"[Search] Total unique diagnosis results: {len(search_results)}")
            
            # REGULAR SEARCH (search_part, product_details, installation_help)
            elif intent in ["search_part", "product_details", "installation_help"]:
                search_results = await self.tools.search_products_by_keyword(
                    keyword=query,
                    category=category,
                    limit=20  # Get more so we can filter by brand
                )
                print(f"[Search] Keyword search found {len(search_results)} results")
                
                # FILTER BY BRAND if specified
                if brand and search_results:
                    original_count = len(search_results)
                    search_results = [
                        p for p in search_results 
                        if p.get('brand', '').lower() == brand.lower()
                    ]
                    print(f"[Search] Filtered by brand '{brand}': {original_count} → {len(search_results)} results")
        
        state["search_results"] = search_results
        
        return state

    async def gather_context(self, state: AgentState) -> AgentState:
        """
        Node 3: Gather additional context using semantic search
        
        Why? Get relevant troubleshooting tips, installation guides, etc.
        """
        
        query = state["user_query"]
        intent = state["intent"]
        
        # Semantic search for relevant docs
        doc_type = None
        if intent == "installation_help":
            doc_type = "installation"
        elif intent == "diagnose_issue":
            doc_type = "troubleshooting"
        
        relevant_docs = await self.tools.semantic_search(
            query=query,
            doc_type=doc_type,
            n_results=5
        )
        
        state["relevant_docs"] = relevant_docs
        
        return state
    async def recommend_parts(self, state: AgentState) -> AgentState:
        """
        Node 4: Use LLM to recommend best parts
        
        
        """
        
        search_results = state.get("search_results", [])
        relevant_docs = state.get("relevant_docs", [])
        user_query = state["user_query"]
        symptoms = state.get("symptoms", [])
        
        if not search_results:
            state["recommended_parts"] = []
            state["reasoning"] = "No products found matching your query."
            return state
        
        # Build context for LLM
        context = {
            "user_query": user_query,
            "symptoms": symptoms,
            "appliance_type": state.get("appliance_type"),
            "model_number": state.get("model_number"),
            "available_products": [
                {
                    "part_number": p["part_number"],
                    "name": p["name"],
                    "price": float(p["price"]),
                    "brand": p["brand"],
                    "in_stock": p["in_stock"]
                }
                for p in search_results[:10]
            ]
        }
        
        # LLM recommendation prompt
        system_prompt = """You are an expert appliance repair technician helping customers find the right parts.

Analyze the user's query and the available products. Recommend the TOP 3 most relevant parts.

Consider:
1. How well the part matches the symptoms
2. Price (prefer affordable options)
3. Brand reputation
4. Availability

Respond in JSON:
{
  "recommended_parts": [
    {
      "part_number": "PS123",
      "relevance_score": 0.95,
      "reason": "This part directly addresses the ice maker not working issue"
    }
  ],
  "overall_reasoning": "Based on your symptoms, these parts are most likely to solve your problem..."
}"""
        
        response = await self.llm.generate(
            prompt=f"Context: {json.dumps(context, indent=2)}",
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse recommendations
        try:
            recommendations = json.loads(response)
            
            recommended_part_numbers = [
                r["part_number"] for r in recommendations["recommended_parts"]
            ]
            
            # Get full details for recommended parts
            recommended_parts = [
                p for p in search_results 
                if p["part_number"] in recommended_part_numbers
            ]
            
            state["recommended_parts"] = recommended_parts
            state["reasoning"] = recommendations.get("overall_reasoning", "")
            
        except:
            # Fallback: recommend top 3 by search ranking
            state["recommended_parts"] = search_results[:3]
            state["reasoning"] = "Here are the most relevant parts based on your search."
        
        return state
    def _clean_product_name(self, name: str, brand: str = None) -> str:
        """
        Remove redundant brand and appliance type from product name
        
        Examples:
        - "Admiral Refrigerator Ice Maker" → "Ice Maker"
        - "Whirlpool Dishwasher Spray Arm" → "Spray Arm"
        - "Samsung Refrigerator Water Filter" → "Water Filter"
        """
        import re
        
        # List of brands to remove
        brands = [
            'Admiral', 'Whirlpool', 'Samsung', 'LG', 'GE', 'Bosch', 
            'Kenmore', 'Frigidaire', 'Maytag', 'KitchenAid', 'Amana',
            'Electrolux', 'Thermador', 'Jenn-Air', 'Roper', 'Estate'
        ]
        
        # List of appliance types to remove
        appliances = [
            'Refrigerator', 'Dishwasher', 'Washer', 'Dryer', 
            'Oven', 'Range', 'Microwave', 'Freezer'
        ]
        
        cleaned = name
        
        # Remove brand names
        for brand_name in brands:
            # Remove at start of string
            cleaned = re.sub(rf'^{brand_name}\s+', '', cleaned, flags=re.IGNORECASE)
            # Remove in middle (brand + appliance)
            cleaned = re.sub(rf'\b{brand_name}\s+', '', cleaned, flags=re.IGNORECASE)
        
        # Remove appliance types
        for appliance in appliances:
            cleaned = re.sub(rf'\b{appliance}\s+', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    async def generate_response(self, state: AgentState) -> AgentState:
        """Node 5: Generate final conversational response"""
        
        intent = state["intent"]
        recommended_parts = state.get("recommended_parts", [])
        reasoning = state.get("reasoning", "")
        user_query = state["user_query"]
        
        # Build response based on intent
        if intent == "search_part":
            response = await self._generate_search_response(
                user_query, recommended_parts, reasoning
            )
        
        elif intent == "product_details":
            response = await self._generate_product_details_response(
                recommended_parts
            )
        
        elif intent == "diagnose_issue":
            response = await self._generate_diagnosis_response(
                user_query, state.get("symptoms", []), recommended_parts, reasoning
            )
        
        elif intent == "installation_help":
            response = await self._generate_installation_response(
                user_query, recommended_parts
            )
        
        elif intent == "compatibility_check":
            response = await self._generate_compatibility_response(
                user_query, state.get("model_number"), recommended_parts
            )
        
        else:
            response = await self._generate_general_response(user_query)
        
        # Add to message history
        state["messages"].append({
            "role": "assistant",
            "content": response
        })
        
        return state
    
    async def _generate_search_response(
    self, 
    query: str, 
    parts: List[Dict], 
    reasoning: str
) -> str:
        """Generate response for part search"""
        
        if not parts:
            return "I couldn't find any parts matching your search. Could you provide more details or try different keywords?"
        
        response = f"{reasoning}\n\n" if reasoning else ""
        response += "Here are the parts I found:\n\n"
        
        for i, part in enumerate(parts[:3], 1):
            clean_name = self._clean_product_name(part['name'], part['brand'])
            response += f"{i}. **{clean_name}** (Part #{part['part_number']})\n"
            response += f"   - Brand: {part['brand']}\n"
            response += f"   - Price: ${part['price']}\n"
            response += f"   - {'✅ In stock' if part['in_stock'] else '❌ Out of stock'}\n"
            
            # ADD PRODUCT LINK
            if part.get('specifications'):
                import json
                specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
                if specs.get('product_url'):
                    response += f"   - 🔗 View: {specs['product_url']}\n"
            
            response += "\n"
        
        response += "Would you like more details about any of these parts?"
        
        return response
    
    async def _generate_diagnosis_response(
    self,
    query: str,
    symptoms: List[str],
    parts: List[Dict],
    reasoning: str
) -> str:
        """Generate response for issue diagnosis"""
        
        if not parts:
            return "I understand you're having an issue, but I need more information. Can you describe what's happening in more detail?"
        
        response = "Based on the symptoms you described, here's what might help:\n\n"
        response += f"{reasoning}\n\n" if reasoning else ""
        response += "**Recommended parts:**\n\n"
        
        for i, part in enumerate(parts[:3], 1):
            clean_name = self._clean_product_name(part['name'], part['brand'])
            response += f"{i}. **{clean_name}** (${part['price']})\n"
            response += f"   Part #: {part['part_number']}\n"
            response += f"   Brand: {part['brand']}\n"
            
            # ADD PRODUCT LINK
            if part.get('specifications'):
                import json
                specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
                if specs.get('product_url'):
                    response += f"   🔗 {specs['product_url']}\n"
            
            response += "\n"
        
        response += "Would you like installation instructions for any of these parts?"
        
        return response
    
    async def _generate_product_details_response(
    self,
    parts: List[Dict]
) -> str:
        """Generate detailed product information response"""
        
        if not parts:
            return "I couldn't find that part number in our database. Could you double-check the part number?"
        
        part = parts[0]
        clean_name = self._clean_product_name(part['name'], part['brand'])
        response = f"**{clean_name}**\n\n"
        response += f"**Part Number:** {part['part_number']}\n"
        response += f"**Price:** ${part['price']}\n"
        response += f"**Brand:** {part['brand']}\n"
        response += f"**Category:** {part['category'].title()}\n"
        response += f"**Availability:** {'✅ In Stock' if part['in_stock'] else '❌ Out of Stock'}\n\n"
        
        # ADD PRODUCT LINK
        if part.get('specifications'):
            import json
            specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
            
            if specs.get('product_url'):
                response += f"**🔗 View on PartSelect:** {specs['product_url']}\n\n"
        
        # Description
        if part.get('description'):
            response += f"**Description:**\n{part['description']}\n\n"
        
        # Specifications
        if part.get('specifications'):
            import json
            specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
            
            if specs.get('replace_parts'):
                replace_parts = specs['replace_parts'][:5]
                response += f"**Compatible Part Numbers:**\n"
                response += ", ".join(replace_parts)
                response += "\n\n"
            
            if specs.get('symptoms'):
                symptoms = specs['symptoms'][:5]
                response += f"**Fixes These Issues:**\n"
                for symptom in symptoms:
                    response += f"• {symptom}\n"
                response += "\n"
        
        # Get installation guide
        guide = await self.tools.get_installation_guide(part['part_number'])
        
        if guide:
            response += f"**Installation Information:**\n"
            response += f"• Difficulty: {guide['difficulty'].title()}\n"
            response += f"• Estimated Time: {guide['estimated_time_minutes']} minutes\n"
            
            if guide.get('video_url'):
                response += f"• 📹 Video Tutorial: {guide['video_url']}\n"
        
        response += "\nNeed help with installation or have questions? Just ask!"
        
        return response

    async def _generate_installation_response(
    self,
    query: str,
    parts: List[Dict]
) -> str:
        """Generate response for installation help"""
        
        if not parts:
            return "I couldn't find that part. Could you provide the part number or try searching for the part first?"
        
        part = parts[0]
        part_number = part["part_number"]
        clean_name = self._clean_product_name(part['name'], part['brand'])
        # Get installation guide
        guide = await self.tools.get_installation_guide(part_number)

        response = f"**Installation Guide for {clean_name}**\n\n"
        response += f"Part Number: {part_number}\n"
        response += f"Price: ${part['price']}\n"
        
        # ADD PRODUCT LINK
        if part.get('specifications'):
            import json
            specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
            if specs.get('product_url'):
                response += f"🔗 Product Page: {specs['product_url']}\n"
        
        response += "\n"
        
        if guide:
            response += f"**Difficulty:** {guide['difficulty'].title()}\n"
            response += f"**Estimated Time:** {guide['estimated_time_minutes']} minutes\n\n"
            
            if guide['tools_required']:
                import json
                tools = json.loads(guide['tools_required']) if isinstance(guide['tools_required'], str) else guide['tools_required']
                response += f"**Tools Needed:** {', '.join(tools)}\n\n"
            
            if guide['video_url']:
                response += f"**📹 Video Tutorial:** {guide['video_url']}\n\n"
                response += "Watch the video for step-by-step visual instructions!\n\n"
            
            if guide['pdf_url']:
                response += f"**📄 PDF Guide:** {guide['pdf_url']}\n\n"
        else:
            response += "⚠️ Detailed installation guide not available for this specific part.\n\n"
            response += "However, general installation tips:\n"
            response += "1. Turn off power/water supply\n"
            response += "2. Remove old part carefully\n"
            response += "3. Clean the area\n"
            response += "4. Install new part following reverse removal steps\n"
            response += "5. Test for proper operation\n\n"
        
        response += f"Stock Status: {'✅ In stock' if part['in_stock'] else '❌ Out of stock'}\n\n"
        response += "Need more help? Feel free to ask!"
        
        return response
    
    async def _generate_compatibility_response(
    self,
    query: str,
    model_number: Optional[str],
    parts: List[Dict]
) -> str:
        """Generate response for compatibility check with smart matching"""
        import json
        
        # Get part number from state or parts
        part = parts[0] if parts else None
        part_number = part['part_number'] if part else None
        
        print(f"[Compatibility] Checking part={part_number} with model={model_number}")
        
        # ========================================
        # SPECIAL CASE: Check if query contains another part number
        # ========================================
        query_codes = re.findall(r"\b(PS\d{7,8}|AP\d{7,8}|W\d{8})\b", query, re.IGNORECASE)
        
        if part and len(query_codes) > 0:
            other_part = query_codes[0].upper()
            
            # Check if the other part is in replace_parts
            if part.get('specifications'):
                specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
                
                if specs.get('replace_parts'):
                    replace_parts_upper = [p.upper() for p in specs['replace_parts']]
                    
                    if other_part in replace_parts_upper:
                        clean_name = self._clean_product_name(part['name'], part['brand'])
                        
                        return f""" **Yes, {other_part} and {part_number} are compatible!**

These parts are listed as compatible replacements for each other.

    Need help with anything else?"""
        
        # ========================================
        # CASE 1: Missing both part and model
        # ========================================
        if not part_number and not model_number:
            return """To check compatibility, I need:
    1. The **part number** (like PS11701542)
    2. Your **appliance model number** (like WRS325SDHZ)

    You can provide both, or if you already mentioned a part, just give me your model number!"""
        
        # ========================================
        # CASE 2: Have part but no model
        # ========================================
        if part_number and not model_number:
            # Check if query has a potential model number
            possible_codes = re.findall(r"\b([A-Z0-9]{6,15})\b", query, re.IGNORECASE)
            
            for candidate in possible_codes:
                candidate_upper = candidate.upper()
                
                # Skip if it's the part number we already have
                if candidate_upper == part_number:
                    continue
                
                # Check if it looks like a part number (not a model)
                if candidate_upper.startswith('PS') or candidate_upper.startswith('W1') or candidate_upper.startswith('AP'):
                    clean_name = self._clean_product_name(part['name'], part['brand'])
                    
                    return f"""I notice you mentioned **{candidate_upper}** - this appears to be a **part number**, not a model number.

    To check compatibility, I need your **appliance's model number**. This is usually found:
    - On a sticker inside the refrigerator door
    - On the back or side of the appliance
    - In your owner's manual

    Model numbers typically look like: **WRS325SDHZ**, **WDT780SAEM1**, **MFI2569VEM2**

    Once you have your model number, I can check if part {part_number} will fit!"""
            
            clean_name = self._clean_product_name(part['name'], part['brand'])
            return f"""To check if **{clean_name}** ({part_number}) will fit, I need your appliance's model number.

    Where to find it:
    - Inside the refrigerator door (on a sticker)
    - On the back or side of the appliance
    - Format: Usually letters and numbers like WRS325SDHZ

    What's your model number?"""
        
        # ========================================
        # CASE 3: Have model but no part
        # ========================================
        if not part_number and model_number:
            return f"""I see your model number is **{model_number}**. Which part would you like to check compatibility for?

    You can provide:
    - A part number (like PS11701542)
    - Or describe the part (like "water filter" or "ice maker")"""
        
        # ========================================
        # CASE 4: Have BOTH part and model - DO COMPATIBILITY CHECK
        # ========================================
        if part_number and model_number:
            return await self._check_detailed_compatibility(part, model_number)


    async def _check_detailed_compatibility(
        self,
        part: Dict,
        model_number: str
    ) -> str:
        """
        Detailed compatibility check using multiple methods
        """
        import json
        
        part_number = part['part_number']
        clean_name = self._clean_product_name(part['name'], part['brand'])
        response = f"**Compatibility Check**\n\n"
        response += f"**Part:** {clean_name} ({part_number})\n"
        response += f"**Your Model:** {model_number}\n"
        response += f"**Price:** ${part['price']}\n"
        
        # Add product link
        if part.get('specifications'):
            specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
            if specs.get('product_url'):
                response += f"🔗 **Product Page:** {specs['product_url']}\n"
        
        response += "\n"
        
        # METHOD 1: Check database compatibility table
        compat = await self.tools.check_compatibility(part_number, model_number)
        
        if compat and compat.get('compatible'):
            response += f"✅ **Yes, this part is compatible with your {model_number}!**\n"
            response += f"Confidence: {int(compat['confidence_score'] * 100)}%\n\n"
            
            if compat.get('notes'):
                response += f"**Note:** {compat['notes']}\n\n"
            
            response += f"Stock Status: {'✅ In stock' if part['in_stock'] else '❌ Out of stock'}\n"
            return response
        
        # METHOD 2: Check if model is in replace_parts or specifications
        if part.get('specifications'):
            specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
            
            # Check if model number appears in replace_parts list
            if specs.get('replace_parts'):
                replace_parts = [p.upper() for p in specs['replace_parts']]
                
                if model_number.upper() in replace_parts:
                    response += f"✅ **Yes, this part is compatible with your {model_number}!**\n\n"
                    response += f"Your model number **{model_number}** is listed as a compatible replacement.\n\n"
                    response += f"Stock Status: {'✅ In stock' if part['in_stock'] else '❌ Out of stock'}\n"
                    return response
            
            # Check if it's a universal part (filters, common components)
            if self._is_universal_part(part, model_number):
                response += f"✅ **This {part['name']} should be compatible with your {model_number}!**\n\n"
                response += f"This is a {part['brand']} {part['category']} part that works with multiple models.\n\n"
                
                if specs.get('replace_parts'):
                    response += f"**Also replaces:** {', '.join(specs['replace_parts'][:8])}\n\n"
                
                response += f"💡 **Tip:** Double-check the product page to confirm your model is listed.\n\n"
                response += f"Stock Status: {'✅ In stock' if part['in_stock'] else '❌ Out of stock'}\n"
                return response
        
        # METHOD 3: Check reverse - is part number in model's compatible parts?
        # (This requires querying by model number, which we might not have)
        
        # If no match found
        response += f"⚠️ **I couldn't confirm compatibility for this combination.**\n\n"
        response += f"This doesn't necessarily mean they're incompatible - I just don't have explicit data.\n\n"
        response += f"**To verify:**\n"
        response += f"1. Check the product page above for compatible models\n"
        response += f"2. Look for your model number ({model_number}) in the specifications\n"
        response += f"3. Contact {part['brand']} support to confirm\n\n"
        response += f"Stock Status: {'✅ In stock' if part['in_stock'] else '❌ Out of stock'}\n"
        
        return response


    def _is_universal_part(self, part: Dict, model_number: str) -> bool:
        """
        Check if part is universal/compatible with many models
        """
        import json
        
        part_name_lower = part['name'].lower()
        
        # Universal filters are almost always compatible within brand
        if 'filter' in part_name_lower:
            # Check if model brand matches part brand
            model_upper = model_number.upper()
            brand_lower = part['brand'].lower()
            
            # Brand prefixes
            brand_prefixes = {
                'whirlpool': ['W', 'WR', 'WD', 'WG'],
                'samsung': ['S', 'RF', 'RS'],
                'lg': ['L', 'LF', 'LM'],
                'ge': ['G', 'GE', 'GD'],
            }
            
            if brand_lower in brand_prefixes:
                for prefix in brand_prefixes[brand_lower]:
                    if model_upper.startswith(prefix):
                        print(f"[Compatibility] Universal filter match: {part['brand']} part for {model_number}")
                        return True
            
            # Check if many replace parts (indicates universal)
            if part.get('specifications'):
                specs = json.loads(part['specifications']) if isinstance(part['specifications'], str) else part['specifications']
                if specs.get('replace_parts') and len(specs['replace_parts']) > 5:
                    return True
        
        return False
    async def _generate_general_response(self, query: str) -> str:
        """Generate response for general questions"""
        
        # Use LLM for general conversation
        system_prompt = """You are a helpful appliance parts assistant. 
Answer the user's question in a friendly, conversational way. 
If you don't know something, admit it and offer to help them search for parts instead."""

        response = await self.llm.generate(
            prompt=query,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=300
        )
        
        return response
    
    async def _generate_llm_response(
        self, 
        context: str, 
        intent: str, 
        user_query: str,
        state: AgentState
    ) -> str:
        """Generate response using LLM"""
        
        # System prompt with brand-specific rules
        system_prompt = """You are a helpful PartSelect assistant helping customers find and install appliance parts.

Guidelines:
- Be conversational and friendly
- Use markdown formatting (**, lists)
- Include product links as: 🔗 [Product Page](URL)
- Keep responses concise (3-4 paragraphs max)
- Use emojis sparingly (🔗, 📹, ✅, ❌)

CRITICAL: Brand-Specific Requests
- If user asks for specific brand (Samsung, Whirlpool, etc.) and we found parts from that brand:
  → List ONLY those brand's parts
  → DO NOT explain why or offer alternatives from other brands
  → DO NOT say "only one option" or "here are alternatives"
  → Just list the parts naturally
  - remove the brand name from the part title to avoid redundancy

- If user asks for specific brand but we found NO parts from that brand:
  → Apologize and explain we don't have that brand currently
  → Offer to show similar parts from other brands

Response patterns:

**search_part with brand specified**:
Just list the parts, no extra explanation needed.

**search_part**:
List parts clearly with details and product links.

**diagnose_issue**: 
Acknowledge problem, explain likely cause, list parts.

**installation_help**: 
Provide guidance, highlight videos, list tools."""

        # Build user prompt
        user_prompt = f"""Context:
{context}

Generate a helpful response to the user's query. Be direct and concise."""

        try:
            # Generate response
            response = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=600
            )
            
            # Check if response asks for model number
            if "model number" in response.lower() and any(word in response.lower() for word in ["need", "provide", "tell me"]):
                state["waiting_for"] = "model_number"
            elif state.get("waiting_for") and state.get("model_number"):
                state["waiting_for"] = None
            
            return response
            
        except Exception as e:
            print(f"[Response] LLM error: {e}")
            return "I apologize, but I encountered an error. Could you please try rephrasing your question?"