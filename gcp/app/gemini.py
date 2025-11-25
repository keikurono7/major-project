import google.generativeai as genai
from typing import Optional, List, Dict, Any
import logging
import time

from app.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self._initialized = True
            logger.info("Gemini AI initialized successfully")
    
    def generate_content(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Generate content with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All retries failed: {e}")
                    return None
    
    def generate_with_context(self, prompt: str, context: List[Dict[str, str]]) -> Optional[str]:
        """Generate content with conversation context"""
        try:
            chat = self.model.start_chat(history=context)
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating with context: {e}")
            return None
    
    def analyze_code(self, code: str, language: str = "python") -> Optional[Dict[str, Any]]:
        """Analyze code quality and provide feedback"""
        prompt = f"""
        Analyze this {language} code and provide:
        1. Code quality score (0-100)
        2. Strengths
        3. Areas for improvement
        4. Security concerns
        5. Performance suggestions
        
        Code:
        ```{language}
        {code}
        ```
        
        Return response in JSON format.
        """
        
        response = self.generate_content(prompt)
        if response:
            try:
                import json
                return json.loads(response)
            except:
                return {"raw_analysis": response}
        return None

# Singleton instance
gemini_client = GeminiClient()