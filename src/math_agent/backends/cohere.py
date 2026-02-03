import logging
import os
from typing import List, Optional

import cohere

from ..config import AgentConfig
from ..types import Message, MessageRole
from .base import LLMBackend

logger = logging.getLogger(__name__)


class CohereBackend(LLMBackend):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "command-r-08-2024",
        config: Optional[AgentConfig] = None,
    ):
        super().__init__(config)
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("COHERE_API_KEY environment variable not set.")

        # Use V2 client for all interactions
        try:
            self.client = cohere.ClientV2(self.api_key)
            self.use_v2 = True
        except AttributeError:
            # Fallback for older SDKs
            self.client = cohere.Client(self.api_key)
            self.use_v2 = False

        self.model = model

    def _generate_impl(
        self,
        system_prompt: str,
        user_prompt: str,
        other_prompts: Optional[List[str]] = None,
        temperature: float = 0.7,
    ) -> str:
        if self.use_v2:
            return self._generate_v2(system_prompt, user_prompt, other_prompts, temperature)
        else:
            return self._generate_v1(system_prompt, user_prompt, other_prompts, temperature)

    def _generate_v2(
        self,
        system_prompt: str,
        user_prompt: str,
        other_prompts: Optional[List[str]],
        temperature: float,
    ) -> str:
        # Build conversation and merge consecutive user messages
        conversation = self.build_conversation(system_prompt, user_prompt, other_prompts)
        conversation = self.merge_consecutive_messages(conversation)

        # Convert to Cohere format
        messages = []
        for msg in conversation:
            messages.append({"role": msg.role.value, "content": msg.content})

        response = self.client.chat(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )

        if response.message and response.message.content:
            content_blocks = response.message.content
            final_text = ""

            if isinstance(content_blocks, list):
                for block in content_blocks:
                    if block.type == "thinking":
                        pass
                    elif block.type == "text":
                        final_text += block.text
            else:
                final_text = str(content_blocks)

            return final_text

        return ""

    def _generate_v1(
        self,
        system_prompt: str,
        user_prompt: str,
        other_prompts: Optional[List[str]],
        temperature: float,
    ) -> str:
        # V1 uses simpler format
        message = user_prompt
        if other_prompts:
            message += "\n\n" + "\n\n".join(other_prompts)

        response = self.client.chat(
            model=self.model,
            message=message,
            preamble=system_prompt,
            temperature=temperature,
        )
        return response.text
