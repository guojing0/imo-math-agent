import logging
from typing import Sequence


logger = logging.getLogger(__name__)

DEFAULT_SOLUTION_MARKERS = [
    "### Detailed Solution ###",
    "## Detailed Solution",
    "Detailed Solution",
]


def extract_detailed_solution(
    text: str,
    markers: Sequence[str] = DEFAULT_SOLUTION_MARKERS,
) -> str:
    """
    Extract the text after a solution marker (e.g. '### Detailed Solution ###').

    Args:
        text: The solution text to extract from.
        markers: Ordered markers to search for; first match wins.

    Returns:
        The text after the marker, or the full text if no marker is found.
    """
    lines = text.split("\n")

    for search_marker in markers:
        for i, line in enumerate(lines):
            if search_marker in line:
                return "\n".join(lines[i + 1 :]).strip()

    logger.warning("Detailed solution marker not found; using full solution.")
    return text.strip()
