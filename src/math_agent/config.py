from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    """Centralized configuration for the Math Agent."""

    solver_temperature: float = 0.7
    verifier_temperature: float = 0.1
    max_verification_iterations: int = 30
    required_consecutive_validations: int = 5
    max_consecutive_errors: int = 10
    max_tokens: int = 8192
    retry_attempts: int = 3
    retry_base_delay: float = 1.0  # Base delay in seconds for exponential backoff
