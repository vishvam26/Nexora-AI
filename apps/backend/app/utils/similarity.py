"""
Module 6: Near Duplicate Detection utility.
Computes token-based overlap similarity to filter duplicate context chunks.
"""


def compute_jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Computes token-level Jaccard overlap similarity.
    """
    if not text_a or not text_b:
        return 0.0

    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())

    intersection = words_a.intersection(words_b)
    union = words_a.union(words_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)
