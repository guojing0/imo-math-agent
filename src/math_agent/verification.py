import re
from .types import VerificationResult


def parse_verification_response(response: str) -> VerificationResult:
    """
    Parse a verification response to determine if the solution is valid.

    Checks for "yes" or "no" indicators in the response text.
    """
    stripped = response.strip()
    text = stripped.lower()

    # Look for a strict final verdict line first
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    for line in reversed(lines):
        lowered = line.lower()
        if lowered in {"final verdict: yes", "final verdict: yes."}:
            return VerificationResult(is_valid=True, bug_report="")
        if lowered in {"final verdict: no", "final verdict: no."}:
            return VerificationResult(is_valid=False, bug_report=response)

    # Exact match
    if text == "yes":
        return VerificationResult(is_valid=True, bug_report="")
    if text == "no":
        return VerificationResult(is_valid=False, bug_report=response)

    # Pattern match at boundaries
    starts_with_yes = text.startswith("yes")
    starts_with_no = text.startswith("no")
    ends_with_yes = text.endswith("yes") or text.endswith("yes.")
    ends_with_no = text.endswith("no") or text.endswith("no.")

    if starts_with_yes or ends_with_yes:
        return VerificationResult(is_valid=True, bug_report="")
    if starts_with_no or ends_with_no:
        return VerificationResult(is_valid=False, bug_report=response)

    # Keyword analysis
    positive_patterns = [
        r"\bcorrect\b",
        r"\bvalid\b",
        r"\baccurate\b",
        r"\bproof is (sound|complete|correct)\b",
        r"\bno (errors?|bugs?|issues?|problems?)\b",
        r"\bsolution is (right|correct|valid)\b",
    ]
    negative_patterns = [
        r"\bincorrect\b",
        r"\binvalid\b",
        r"\berror\b",
        r"\bbug\b",
        r"\bflaw\b",
        r"\bmistake\b",
        r"\bwrong\b",
        r"\bfail(ed|s)?\b",
        r"\bgap\b",
        r"\bmissing\b",
        r"\bunjustified\b",
    ]

    positive_count = sum(
        1 for pattern in positive_patterns if re.search(pattern, text)
    )
    negative_count = sum(
        1 for pattern in negative_patterns if re.search(pattern, text)
    )

    if positive_count > negative_count:
        return VerificationResult(is_valid=True, bug_report="")
    elif negative_count > positive_count:
        return VerificationResult(is_valid=False, bug_report=response)

    # Fallback: check for simple "yes" or "no" anywhere
    if "yes" in text and "no" not in text:
        return VerificationResult(is_valid=True, bug_report="")
    if "no" in text and "yes" not in text:
        return VerificationResult(is_valid=False, bug_report=response)

    # Ambiguous: default to invalid to be safe
    return VerificationResult(
        is_valid=False,
        bug_report=f"Ambiguous verification response: {response}",
    )


def summarize_verification(
    decision_response: str, verification_log: str
) -> VerificationResult:
    """
    Convert the verifier decision response into a final VerificationResult.

    Uses the detailed verification log as the bug report when invalid.
    """
    decision = parse_verification_response(decision_response)
    if decision.is_valid:
        return decision
    return VerificationResult(is_valid=False, bug_report=verification_log)
