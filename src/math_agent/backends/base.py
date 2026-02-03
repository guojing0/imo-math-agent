from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, other_prompts: Optional[List[str]] = None, temperature: float = 0.7) -> str:
        """Generates text from the model."""
        pass
