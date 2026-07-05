"""
Token counting and budget management utilities for RAG context assembly.
"""


def count_tokens(text: str) -> int:
    """
    Estimates GPT-style token count (~4 chars per token).
    Accurate enough for context budget management without needing tiktoken.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def truncate_to_budget(text: str, max_tokens: int) -> str:
    """
    Truncates text so its estimated token count fits within max_tokens.
    Truncates at a word boundary where possible.
    """
    if count_tokens(text) <= max_tokens:
        return text

    max_chars = max_tokens * 4
    truncated = text[:max_chars]

    # Try to cut at last space to avoid mid-word truncation
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]

    return truncated + " ..."


def fits_within_budget(text: str, max_tokens: int) -> bool:
    return count_tokens(text) <= max_tokens
