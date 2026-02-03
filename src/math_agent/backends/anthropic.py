import os
from typing import List, Optional

import anthropic

from ..config import AgentConfig
from ..types import MessageRole
from .base import LLMBackend


class AnthropicBackend(LLMBackend):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20240620",
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(config)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def _generate_impl(
        self,
        system_prompt: str,
        user_prompt: str,
        other_prompts: Optional[List[str]] = None,
        temperature: float = 0.7,
    ) -> str:
        # Build conversation - exclude system from messages (Anthropic uses separate param)
        conversation = self.build_conversation("", user_prompt, other_prompts)
        # Merge consecutive user messages (Anthropic requires alternating roles)
        conversation = self.merge_consecutive_messages(conversation)

        # Convert to Anthropic format
        messages = []
        for msg in conversation:
            messages.append({"role": msg.role.value, "content": msg.content})

        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=temperature,
        )

        return response.content[0].text
