"""
Module 5: Context Compression text truncation helper.
"""


def compress_text(text: str, max_chars: int) -> str:
    """
    Strips extra whitespaces and truncates if length exceeds limit.
    """
    if not text:
        return ""
    import re
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + " ... [Compressed]"
