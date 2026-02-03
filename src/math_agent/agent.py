import logging
from typing import List, Optional

from .backends.base import LLMBackend
from .config import AgentConfig
from .prompts import (
    CORRECTION_PROMPT,
    SELF_IMPROVEMENT_PROMPT,
    STEP1_PROMPT,
    VERIFICATION_REMINDER,
    VERIFICATION_SYSTEM_PROMPT,
)
from .types import VerificationResult
from .utils import extract_detailed_solution
from .verification import parse_verification_response

logger = logging.getLogger(__name__)


class MathAgent:
    def __init__(
        self,
        backend: LLMBackend,
        verifier_backend: Optional[LLMBackend] = None,
        config: Optional[AgentConfig] = None,
    ):
        self.backend = backend
        self.verifier_backend = verifier_backend or backend
        self.config = config or AgentConfig()

    def solve(
        self,
        problem_statement: str,
        other_prompts: Optional[List[str]] = None,
        max_iterations: Optional[int] = None,
    ) -> Optional[str]:
        """
        Solve a math problem using iterative refinement and verification.

        Args:
            problem_statement: The problem to solve.
            other_prompts: Additional prompts/hints to include.
            max_iterations: Override for max verification iterations.

        Returns:
            The verified solution, or None if no valid solution was found.
        """
        max_iter = max_iterations or self.config.max_verification_iterations
        logger.info("Starting solution process...")

        # 1. Initial Exploration
        solution = self._initial_exploration(problem_statement, other_prompts)
        if not solution:
            logger.error("Failed to generate initial solution.")
            return None

        # 2. Self Improvement
        solution = self._self_improvement(problem_statement, solution, other_prompts)

        # 3. Initial Verification
        verification = self._verify_solution(problem_statement, solution)
        logger.info(f"Initial Verification Valid: {verification.is_valid}")

        correct_count = 1 if verification.is_valid else 0
        error_count = 0

        # 4. Verification Loop
        for i in range(max_iter):
            logger.info(
                f"Iteration {i+1}/{max_iter} - "
                f"Correct Streak: {correct_count}, Errors: {error_count}"
            )

            if not verification.is_valid:
                correct_count = 0
                error_count += 1
                logger.info("Verification failed. Attempting correction...")

                solution = self._correct_solution(
                    problem_statement, solution, verification.bug_report, other_prompts
                )

            # Re-verify
            verification = self._verify_solution(problem_statement, solution)

            if verification.is_valid:
                correct_count += 1
                error_count = 0
                logger.info(
                    f"Solution verified as valid "
                    f"(confidence: {verification.confidence:.2f}). "
                    f"Streak: {correct_count}"
                )

            if correct_count >= self.config.required_consecutive_validations:
                logger.info(
                    f"Solution verified {self.config.required_consecutive_validations} "
                    f"times consecutively. SUCCESS."
                )
                return solution

            if error_count >= self.config.max_consecutive_errors:
                logger.info("Too many consecutive errors. FAILURE.")
                return None

        logger.info("Max iterations reached without success.")
        return None

    def _initial_exploration(
        self, problem_statement: str, other_prompts: Optional[List[str]]
    ) -> str:
        logger.info("Generating initial solution...")
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=problem_statement,
            other_prompts=other_prompts,
            temperature=self.config.solver_temperature,
        )

    def _self_improvement(
        self,
        problem_statement: str,
        current_solution: str,
        other_prompts: Optional[List[str]],
    ) -> str:
        logger.info("Self-improving solution...")
        combined_prompt = (
            f"Problem:\n{problem_statement}\n\n"
            f"Proposed Solution:\n{current_solution}\n\n"
            f"{SELF_IMPROVEMENT_PROMPT}"
        )
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=combined_prompt,
            other_prompts=other_prompts,
            temperature=self.config.solver_temperature,
        )

    def _verify_solution(
        self, problem_statement: str, solution: str
    ) -> VerificationResult:
        dsol = extract_detailed_solution(solution)
        verification_prompt = f"""
======================================================================
### Problem ###

{problem_statement}

======================================================================
### Solution ###

{dsol}

{VERIFICATION_REMINDER}
"""
        # Step 1: Generate verification log
        verification_log = self.verifier_backend.generate(
            system_prompt=VERIFICATION_SYSTEM_PROMPT,
            user_prompt=verification_prompt,
            temperature=self.config.verifier_temperature,
        )

        # Step 2: Check if verification is positive
        check_prompt = (
            'Response in "yes" or "no". '
            "Is the following statement saying the solution is correct, "
            "or does not contain critical error or a major justification gap?\n\n"
            f"{verification_log}"
        )

        check_response = self.verifier_backend.generate(
            system_prompt="",
            user_prompt=check_prompt,
            temperature=self.config.verifier_temperature,
        )

        # Use robust parsing instead of simple string matching
        result = parse_verification_response(check_response)

        # If invalid, include the full verification log as bug report
        if not result.is_valid:
            return VerificationResult(
                is_valid=False,
                confidence=result.confidence,
                bug_report=verification_log,
            )

        return result

    def _correct_solution(
        self,
        problem_statement: str,
        current_solution: str,
        bug_report: str,
        other_prompts: Optional[List[str]],
    ) -> str:
        combined_prompt = (
            f"Problem:\n{problem_statement}\n\n"
            f"Proposed Solution:\n{current_solution}\n\n"
            f"Bug Report:\n{bug_report}\n\n"
            f"{CORRECTION_PROMPT}"
        )

        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=combined_prompt,
            other_prompts=other_prompts,
            temperature=self.config.solver_temperature,
        )
