import re

def extract_detailed_solution(text: str, marker: str = "Detailed Solution", after: bool = True) -> str:
    """
    Extracts the text after '### Detailed Solution ###' (or similar marker) from the solution string.
    """
    # Robust finding of the marker (ignoring case or exact ###)
    # The prompt asks for "**2. Detailed Solution**" or "### Detailed Solution ###" depending on formatting.
    # The IMO25 code searched for literal marker.
    
    # Let's try to find the marker line.
    lines = text.split('\n')
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
            return text[pos + len(marker):].strip()
        else:
            return text[:pos].strip()

    if after:
        return "\n".join(lines[idx+1:]).strip()
    else:
        return "\n".join(lines[:idx]).strip()

def extract_code_blocks(text: str) -> list[str]:
    """Extracts code blocks from text."""
    pattern = r"```(?:\w+)?\n(.*?)```"
    return re.findall(pattern, text, re.DOTALL)

