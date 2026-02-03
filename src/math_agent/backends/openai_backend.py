import os
from typing import List, Optional
from openai import OpenAI
from .base import LLMBackend

class OpenAIBackend(LLMBackend):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, other_prompts: Optional[List[str]] = None, temperature: float = 0.7) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if other_prompts:
            for prompt in other_prompts:
                messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        
        return response.choices[0].message.content
