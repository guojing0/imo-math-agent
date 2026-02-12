from .prompts import CORRECTION_PROMPT, SELF_IMPROVEMENT_PROMPT, VERIFICATION_REMINDER


def build_self_improvement_prompt(problem_statement: str, current_solution: str) -> str:
    return (
        f"Problem:\n{problem_statement}\n\n"
        f"Proposed Solution:\n{current_solution}\n\n"
        f"{SELF_IMPROVEMENT_PROMPT}"
    )


def build_correction_prompt(
    problem_statement: str, current_solution: str, bug_report: str
) -> str:
    return (
        f"Problem:\n{problem_statement}\n\n"
        f"Proposed Solution:\n{current_solution}\n\n"
        f"Bug Report:\n{bug_report}\n\n"
        f"{CORRECTION_PROMPT}"
    )


def build_verification_prompt(problem_statement: str, detailed_solution: str) -> str:
    return f"""
======================================================================
### Problem ###

{problem_statement}

======================================================================
### Solution ###

{detailed_solution}

{VERIFICATION_REMINDER}
"""
