"""
LLM Client - DeepSeek Integration

Handles all LLM interactions with proper error handling and retries
"""

import httpx
from typing import Optional, Dict, List
from app.config import get_settings
import asyncio
import json

settings = get_settings()


class DeepSeekClient:
    """
    DeepSeek API Client
    
    Why DeepSeek?
    - Cost effective ($0.14/M tokens input, $0.28/M tokens output)
    - Fast inference
    - Good reasoning capabilities
    - Compatible with OpenAI API format
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
        # HTTP client with retry logic
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.95,
        stream: bool = False
    ) -> str:
        """
        Generate a completion
        
        Args:
            prompt: User message
            system_prompt: System instructions
            temperature: 0.0 = deterministic, 1.0 = creative
            max_tokens: Maximum response length
            top_p: Nucleus sampling
            stream: Whether to stream response
        
        Returns:
            Generated text
        """
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Extract content
            content = result["choices"][0]["message"]["content"]
            
            return content
        
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            raise
    
    async def generate_with_chat_history(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate with full chat history
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            temperature: Sampling temperature
            max_tokens: Max response length
        
        Returns:
            Generated response
        """
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Error in chat completion: {e}")
            raise
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.3
    ) -> Dict:
        """
        Generate structured JSON output
        
        Why lower temperature? More consistent JSON formatting
        
        Args:
            prompt: User message
            system_prompt: System instructions (should specify JSON format)
            temperature: Lower = more consistent
        
        Returns:
            Parsed JSON dict
        """
        
        # Add JSON instruction to system prompt
        enhanced_system = system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation, just JSON."
        
        response = await self.generate(
            prompt=prompt,
            system_prompt=enhanced_system,
            temperature=temperature,
            max_tokens=1000
        )
        
        # Clean response (remove markdown if present)
        cleaned = response.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {cleaned[:200]}...")
            print(f"Error: {e}")
            # Return empty dict as fallback
            return {}
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global client instance
_llm_client: Optional[DeepSeekClient] = None


def get_llm_client() -> DeepSeekClient:
    """
    Get or create LLM client
    
    Why global? Reuse HTTP connections for better performance
    """
    global _llm_client
    
    if _llm_client is None:
        _llm_client = DeepSeekClient(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model=settings.DEEPSEEK_MODEL
        )
    
    return _llm_client


async def close_llm_client():
    """Close LLM client on shutdown"""
    global _llm_client
    if _llm_client:
        await _llm_client.close()
        _llm_client = None