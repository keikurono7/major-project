import httpx
from typing import Optional, List, Dict, Any
import logging
import time
import json

from app.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.base_url = settings.OLLAMA_BASE_URL
            self.model = settings.OLLAMA_MODEL
            self.client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)
            self._initialized = True
            logger.info(f"Ollama client initialized with model: {self.model}")
    
    async def generate_content(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Generate content with retry logic"""
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All retries failed: {e}")
                    return None
    
    async def generate_with_context(self, prompt: str, context: List[Dict[str, str]]) -> Optional[str]:
        """Generate content with conversation context"""
        try:
            # Build conversation history
            messages = []
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("parts", [""])[0] if "parts" in msg else msg.get("content", "")
                messages.append({"role": role, "content": content})
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"Error generating with context: {e}")
            return None
    
    async def analyze_code(self, code: str, language: str = "python") -> Optional[Dict[str, Any]]:
        """Analyze code quality and provide feedback"""
        prompt = f"""
        Analyze this {language} code and provide a detailed evaluation.
        
        Code:
        ```{language}
        {code}
        ```
        
        Provide your analysis in JSON format with the following structure:
        {{
            "code_quality_score": <0-100>,
            "strengths": ["list of strengths"],
            "improvements": ["list of areas for improvement"],
            "security_concerns": ["list of security issues if any"],
            "performance_suggestions": ["list of performance tips"],
            "best_practices": ["list of best practices to follow"]
        }}
        
        Only return valid JSON, no additional text.
        """
        
        response = await self.generate_content(prompt)
        if response:
            try:
                # Try to extract JSON from response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
                return {"raw_analysis": response}
            except json.JSONDecodeError:
                return {"raw_analysis": response}
        return None
    
    async def check_health(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Singleton instance
ollama_client = OllamaClient()