import logging
from app.utils.compression import compress_text
from app.utils.token_counter import count_tokens

logger = logging.getLogger("app.services.compression_service")


class CompressionService:
    """
    Module 5: Context Compression
    Prunes retrieved chunk segments to prevent token limits overflow.
    """

    @staticmethod
    def compress_chunks(chunks: list, max_tokens: int = 2000) -> list:
        """
        Compresses text elements of chunks if combined token count exceeds max_tokens.
        """
        total_tokens = sum(c.get("token_count", 0) for c in chunks)
        if total_tokens <= max_tokens:
            return chunks

        logger.info(f"RAG: Compressing {len(chunks)} chunks to fit within {max_tokens} tokens budget")
        compressed_list = []
        max_chars_per_chunk = int((max_tokens * 4) / max(1, len(chunks)))

        for chunk in chunks:
            chunk_copy = dict(chunk)
            chunk_copy["text"] = compress_text(chunk.get("text", ""), max_chars_per_chunk)
            chunk_copy["token_count"] = count_tokens(chunk_copy["text"])
            compressed_list.append(chunk_copy)

        return compressed_list
