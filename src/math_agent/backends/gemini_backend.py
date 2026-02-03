import os
from typing import List, Optional
from google import genai
from google.genai import types
from .base import LLMBackend

class GeminiBackend(LLMBackend):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, other_prompts: Optional[List[str]] = None, temperature: float = 0.7) -> str:
        
        message_parts = [user_prompt]
        if other_prompts:
            message_parts.extend(other_prompts)
            
        content = "\n\n".join(message_parts)

        response = self.client.models.generate_content(
            model=self.model,
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature
            )
        )
        
        return response.text