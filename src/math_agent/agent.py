import json
import logging
from typing import Optional, List, Tuple
from .backends.base import LLMBackend
from .prompts import (
    STEP1_PROMPT,
    SELF_IMPROVEMENT_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    CHECK_VERIFICATION_PROMPT,
    CORRECTION_PROMPT,
    VERIFICATION_REMINDER
)
from .utils import extract_detailed_solution

logger = logging.getLogger(__name__)

class MathAgent:
    def __init__(self, backend: LLMBackend, verifier_backend: Optional[LLMBackend] = None):
        self.backend = backend
        self.verifier_backend = verifier_backend or backend

    def solve(self, problem_statement: str, other_prompts: Optional[List[str]] = None, max_iterations: int = 30) -> Optional[str]:
        logger.info("Starting solution process...")
        
        # 1. Initial Exploration
        solution = self._initial_exploration(problem_statement, other_prompts)
        if not solution:
            logger.error("Failed to generate initial solution.")
            return None

        # 2. Self Improvement
        solution = self._self_improvement(problem_statement, solution, other_prompts)
        
        # 3. Initial Verification
        bug_report, is_valid = self._verify_solution(problem_statement, solution)
        logger.info(f"Initial Verification Valid: {is_valid}")

        correct_count = 1 if is_valid else 0
        error_count = 0

        # 4. Verification Loop
        for i in range(max_iterations):
            logger.info(f"Iteration {i+1}/{max_iterations} - Correct Streak: {correct_count}, Errors: {error_count}")
            
            if not is_valid:
                correct_count = 0
                error_count += 1
                logger.info("Verification failed. Attempting correction...")
                
                solution = self._correct_solution(problem_statement, solution, bug_report, other_prompts)
            
            # Re-verify
            bug_report, is_valid = self._verify_solution(problem_statement, solution)
            
            if is_valid:
                correct_count += 1
                error_count = 0
                logger.info(f"Solution verified as valid. Streak: {correct_count}")
            
            if correct_count >= 5:
                logger.info("Solution verified 5 times consecutively. SUCCESS.")
                return solution
            
            if error_count >= 10:
                logger.info("Too many consecutive errors. FAILURE.")
                return None

        logger.info("Max iterations reached without success.")
        return None

    def _initial_exploration(self, problem_statement: str, other_prompts: Optional[List[str]]) -> str:
        logger.info("Generating initial solution...")
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=problem_statement,
            other_prompts=other_prompts,
            temperature=0.7
        )

    def _self_improvement(self, problem_statement: str, current_solution: str, other_prompts: Optional[List[str]]) -> str:
        logger.info("Self-improving solution...")
        # To strictly follow IMO25 logic:
        # It appends the current solution as a model response, then adds the self-improvement prompt.
        # Our backend 'other_prompts' usually appends user messages.
        # We need to simulate: User (Problem) -> Model (Solution) -> User (Self Improve)
        # For simplicity/statelessness: We construct a new chain.
        
        combined_prompt = f"Problem:\n{problem_statement}\n\nProposed Solution:\n{current_solution}\n\n{SELF_IMPROVEMENT_PROMPT}"
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=combined_prompt,
            other_prompts=other_prompts, # These might be extra hints
            temperature=0.7
        )

    def _verify_solution(self, problem_statement: str, solution: str) -> Tuple[str, bool]:
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
            temperature=0.1 # Lower temp for verification
        )
        
        # Step 2: Check if verification is positive
        check_prompt = f"Response in \"yes\" or \"no\". Is the following statement saying the solution is correct, or does not contain critical error or a major justification gap?\n\n{verification_log}"
        
        check_response = self.verifier_backend.generate(
            system_prompt="",
            user_prompt=check_prompt,
            temperature=0.1
        )
        
        is_valid = "yes" in check_response.lower()
        
        bug_report = ""
        if not is_valid:
            # Extract bug report from the log (usually the summary or findings)
            # IMO25 extracts "Detailed Verification" part but logic was slightly complex.
            # I'll just return the full log as the bug report for the agent to analyze.
            bug_report = verification_log

        return bug_report, is_valid

    def _correct_solution(self, problem_statement: str, current_solution: str, bug_report: str, other_prompts: Optional[List[str]]) -> str:
        # Construct correction prompt
        # User (Problem) -> Model (Solution) -> User (Bug Report + Correction Instruction)
        
        combined_prompt = f"Problem:\n{problem_statement}\n\nProposed Solution:\n{current_solution}\n\nBug Report:\n{bug_report}\n\n{CORRECTION_PROMPT}"
        
        return self.backend.generate(
            system_prompt=STEP1_PROMPT,
            user_prompt=combined_prompt,
            other_prompts=other_prompts,
            temperature=0.7
        )
