import os
from typing import Optional

from google import genai
from google.genai import types

from ..config import AgentConfig
from ..types import MessageRole
from .base import LLMBackend


class GeminiBackend(LLMBackend):
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(config)
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def _generate_impl(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        conversation = self.build_conversation("", user_prompt)

        # Convert to Gemini multi-turn format
        # Gemini expects list of Content objects with parts
        contents = []
        for msg in conversation:
            # Map MessageRole to Gemini role names
            role = "user" if msg.role == MessageRole.USER else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg.content)],
                )
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
            ),
        )

        return response.text or ""
