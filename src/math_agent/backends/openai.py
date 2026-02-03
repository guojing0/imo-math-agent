import os
from typing import List, Optional

from openai import OpenAI

from ..config import AgentConfig
from ..types import MessageRole
from .base import LLMBackend


class OpenAIBackend(LLMBackend):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(config)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def _generate_impl(
        self,
        system_prompt: str,
        user_prompt: str,
        other_prompts: Optional[List[str]] = None,
        temperature: float = 0.7,
    ) -> str:
        # Build conversation and merge consecutive user messages
        conversation = self.build_conversation(system_prompt, user_prompt, other_prompts)
        conversation = self.merge_consecutive_messages(conversation)

        # Convert to OpenAI format
        messages = []
        for msg in conversation:
            messages.append({"role": msg.role.value, "content": msg.content})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=self.config.max_tokens,
        )

        return response.choices[0].message.content or ""
