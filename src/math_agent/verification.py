import re
from .types import VerificationResult

_VERDICT_RE = re.compile(r"^final\s+verdict\s*:\s*(yes|no)\s*\.?\s*$", re.IGNORECASE)

_POSITIVE_PATTERNS = [
    re.compile(p)
    for p in [
        r"\bcorrect\b",
        r"\bvalid\b",
        r"\baccurate\b",
        r"\bproof is (sound|complete|correct)\b",
        r"\bno (errors?|bugs?|issues?|problems?)\b",
        r"\bsolution is (right|correct|valid)\b",
    ]
]

_NEGATIVE_PATTERNS = [
    re.compile(p)
    for p in [
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
]


def parse_verification_response(response: str) -> VerificationResult:
    """
    Parse a verification response to determine if the solution is valid.

    Checks for "yes" or "no" indicators in the response text.
    """
    stripped = response.strip()
    text = stripped.lower()

    # Exact match short-circuit
    if text == "yes":
        return VerificationResult(is_valid=True, bug_report="")
    if text == "no":
        return VerificationResult(is_valid=False, bug_report=response)

    # Look for a strict final verdict line
    for line in reversed(stripped.splitlines()):
        m = _VERDICT_RE.match(line.strip())
        if m:
            is_yes = m.group(1).lower() == "yes"
            return VerificationResult(
                is_valid=is_yes, bug_report="" if is_yes else response
            )

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
    positive_count = sum(1 for p in _POSITIVE_PATTERNS if p.search(text))
    negative_count = sum(1 for p in _NEGATIVE_PATTERNS if p.search(text))

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
