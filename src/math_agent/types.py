from dataclasses import dataclass
from enum import Enum
from typing import List


class MessageRole(Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A single message in a conversation."""

    role: MessageRole
    content: str


# Type alias for a conversation
Conversation = List[Message]


@dataclass
class VerificationResult:
    """Result of verifying a solution."""

    is_valid: bool
    confidence: float  # 0.0 to 1.0
    bug_report: str  # Empty if is_valid is True
