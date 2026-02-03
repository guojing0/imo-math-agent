import re
from .types import VerificationResult


def parse_verification_response(response: str) -> VerificationResult:
    """
    Parse a verification response using multiple strategies.

    Strategies (in order of confidence):
    1. Exact match: "yes" or "no" as the entire response (trimmed)
    2. Pattern match: "yes" or "no" at start/end of response
    3. Keyword analysis: count positive vs negative indicators
    """
    text = response.strip().lower()

    # Strategy 1: Exact match (highest confidence)
    if text == "yes":
        return VerificationResult(is_valid=True, confidence=1.0, bug_report="")
    if text == "no":
        return VerificationResult(is_valid=False, confidence=1.0, bug_report=response)

    # Strategy 2: Pattern match at boundaries
    # Check for "yes" or "no" at the start or end
    starts_with_yes = text.startswith("yes")
    starts_with_no = text.startswith("no")
    ends_with_yes = text.endswith("yes") or text.endswith("yes.")
    ends_with_no = text.endswith("no") or text.endswith("no.")

    if starts_with_yes or ends_with_yes:
        confidence = 0.9 if starts_with_yes else 0.8
        return VerificationResult(is_valid=True, confidence=confidence, bug_report="")
    if starts_with_no or ends_with_no:
        confidence = 0.9 if starts_with_no else 0.8
        return VerificationResult(is_valid=False, confidence=confidence, bug_report=response)

    # Strategy 3: Keyword analysis
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

    # Decision based on keyword balance
    if positive_count > negative_count:
        # More positive indicators
        confidence = min(0.7, 0.5 + 0.1 * (positive_count - negative_count))
        return VerificationResult(is_valid=True, confidence=confidence, bug_report="")
    elif negative_count > positive_count:
        # More negative indicators
        confidence = min(0.7, 0.5 + 0.1 * (negative_count - positive_count))
        return VerificationResult(
            is_valid=False, confidence=confidence, bug_report=response
        )

    # Fallback: check for simple "yes" or "no" anywhere (lowest confidence)
    if "yes" in text and "no" not in text:
        return VerificationResult(is_valid=True, confidence=0.4, bug_report="")
    if "no" in text and "yes" not in text:
        return VerificationResult(is_valid=False, confidence=0.4, bug_report=response)

    # Truly ambiguous: default to invalid to be safe
    return VerificationResult(
        is_valid=False,
        confidence=0.3,
        bug_report=f"Ambiguous verification response: {response}",
    )
