def extract_detailed_solution(
    text: str, marker: str = "Detailed Solution", after: bool = True
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
    lines = text.split("\n")
    idx = -1
    for i, line in enumerate(lines):
        if marker in line:
            idx = i
            break

    if idx == -1:
        # Fallback to string search
        pos = text.find(marker)
        if pos == -1:
            return "" if after else text
        if after:
            return text[pos + len(marker) :].strip()
        else:
            return text[:pos].strip()

    if after:
        return "\n".join(lines[idx + 1 :]).strip()
    else:
        return "\n".join(lines[:idx]).strip()

