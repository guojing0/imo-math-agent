import logging
from typing import Iterable, Optional


logger = logging.getLogger(__name__)


def extract_detailed_solution(
    text: str,
    marker: str = "Detailed Solution",
    after: bool = True,
    markers: Optional[Iterable[str]] = None,
) -> str:
    """
    Extract the text after '### Detailed Solution ###' (or similar marker) from a solution.

    Args:
        text: The solution text to extract from.
        marker: The marker to search for.
        after: If True, return text after the marker; if False, return text before.

    Returns:
        The extracted text, or empty string if marker not found (when after=True).
    """
    search_markers = list(markers) if markers is not None else [marker]
    lines = text.split("\n")

    for search_marker in search_markers:
        for i, line in enumerate(lines):
            if search_marker in line:
                if after:
                    return "\n".join(lines[i + 1 :]).strip()
                return "\n".join(lines[:i]).strip()

        # Fallback to string search for inline markers
        pos = text.find(search_marker)
        if pos != -1:
            if after:
                return text[pos + len(search_marker) :].strip()
            return text[:pos].strip()

    if after:
        logger.warning("Detailed solution marker not found; using full solution.")
    return text.strip()
