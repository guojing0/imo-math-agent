import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from ..config import AgentConfig
from ..types import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


class LLMBackend(ABC):
    """Base class for LLM backends with retry logic."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text from the model with automatic retry logic.

        This method wraps _generate_impl with exponential backoff retry.
        """
        last_exception = None

        for attempt in range(self.config.retry_attempts):
            try:
                return self._generate_impl(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                )
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_base_delay * (2**attempt)
                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{self.config.retry_attempts}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"API call failed after {self.config.retry_attempts} attempts: {e}"
                    )

        raise last_exception  # type: ignore

    @abstractmethod
    def _generate_impl(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        """Actual implementation of text generation. Subclasses must implement this."""
        pass

    def build_conversation(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Conversation:
        """
        Build a standardized conversation from prompts.

        Creates a properly structured conversation with:
        - System message (if provided)
        - User message
        """
        messages: Conversation = []

        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))

        messages.append(Message(role=MessageRole.USER, content=user_prompt))

        return messages
