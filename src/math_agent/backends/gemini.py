import os
from typing import List, Optional

from google import genai
from google.genai import types

from ..config import AgentConfig
from ..types import MessageRole
from .base import LLMBackend


class GeminiBackend(LLMBackend):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
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
        other_prompts: Optional[List[str]] = None,
        temperature: float = 0.7,
    ) -> str:
        # Build conversation and merge consecutive messages
        conversation = self.build_conversation("", user_prompt, other_prompts)
        conversation = self.merge_consecutive_messages(conversation)

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
