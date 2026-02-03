import os
from typing import List, Optional
import anthropic
from .base import LLMBackend

class AnthropicBackend(LLMBackend):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, other_prompts: Optional[List[str]] = None, temperature: float = 0.7) -> str:
        messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        if other_prompts:
            for prompt in other_prompts:
                messages.append({"role": "user", "content": prompt})

        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=4096,
            temperature=temperature
        )
        
        return response.content[0].text
