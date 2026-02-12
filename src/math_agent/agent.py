import logging
from typing import Optional

from .backends.base import LLMBackend
from .config import AgentConfig
from .prompting import (
    build_correction_prompt,
    build_self_improvement_prompt,
    build_verification_prompt,
)
from .prompts import (
    STEP1_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
)
from .types import VerificationResult
from .utils import extract_detailed_solution
from .verification import summarize_verification

logger = logging.getLogger(__name__)


class MathAgent:
    DETAILED_SOLUTION_MARKERS = [
        "### Detailed Solution ###",
        "## Detailed Solution",
        "Detailed Solution",
    ]

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
        max_iterations: Optional[int] = None,
    ) -> Optional[str]:
        """
        Solve a math problem using iterative refinement and verification.

        Args:
            problem_statement: The problem to solve.
            max_iterations: Override for max verification iterations.

        Returns:
            The verified solution, or None if no valid solution was found.
        """
        max_iter = max_iterations or self.config.max_verification_iterations
        logger.info("Starting solution process...")

        # 1. Initial Exploration
        solution = self._initial_exploration(problem_statement)
        if not solution:
            logger.error("Failed to generate initial solution.")
            return None

        # 2. Self Improvement
        solution = self._self_improvement(problem_statement, solution)

        # 3. Initial Verification
        verification = self._verify_solution(problem_statement, solution)
        logger.info("Initial verification valid: %s", verification.is_valid)

        correct_count = 1 if verification.is_valid else 0
        error_count = 0

        # 4. Verification Loop
        for i in range(max_iter):
            logger.info(
                "Iteration %s/%s - Correct streak: %s, Errors: %s",
                i + 1,
                max_iter,
                correct_count,
                error_count,
            )

            if not verification.is_valid:
                correct_count = 0
                error_count += 1
                logger.info("Verification failed. Attempting correction...")

                solution = self._correct_solution(
                    problem_statement, solution, verification.bug_report
                )

            # Re-verify
            verification = self._verify_solution(problem_statement, solution)

            if verification.is_valid:
                correct_count += 1
                error_count = 0
                logger.info("Solution verified as valid. Streak: %s", correct_count)

            if correct_count >= self.config.required_consecutive_validations:
                logger.info(
                    "Solution verified %s times consecutively. SUCCESS.",
                    self.config.required_consecutive_validations,
                )
                return solution

            if error_count >= self.config.max_consecutive_errors:
                logger.info("Too many consecutive errors. FAILURE.")
                return None

        logger.info("Max iterations reached without success.")
        return None

    def _initial_exploration(self, problem_statement: str) -> str:
        logger.info("Generating initial solution...")
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=problem_statement,
            temperature=self.config.solver_temperature,
        )

    def _self_improvement(
        self,
        problem_statement: str,
        current_solution: str,
    ) -> str:
        logger.info("Self-improving solution...")
        combined_prompt = build_self_improvement_prompt(
            problem_statement, current_solution
        )
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=combined_prompt,
            temperature=self.config.solver_temperature,
        )

    def _verify_solution(
        self, problem_statement: str, solution: str
    ) -> VerificationResult:
        dsol = extract_detailed_solution(
            solution, markers=self.DETAILED_SOLUTION_MARKERS
        )
        verification_prompt = build_verification_prompt(problem_statement, dsol)
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

        # Use robust parsing with strict verdict first
        return summarize_verification(check_response, verification_log)

    def _correct_solution(
        self,
        problem_statement: str,
        current_solution: str,
        bug_report: str,
    ) -> str:
        combined_prompt = build_correction_prompt(
            problem_statement, current_solution, bug_report
        )

        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=combined_prompt,
            temperature=self.config.solver_temperature,
        )
