import os
import sys

# Load env
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

sys.path.append(backend_dir)

# Import models
import app.db.base

from app.db.session import SessionLocal
from app.services.vector_store.qdrant_vector_store import QdrantVectorStore
from app.services.embedding.embedding_service import EmbeddingService
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.keyword_service import KeywordService
from app.services.hybrid_search_service import HybridSearchService
from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
from app.config import settings

# For trace:
from app.services.query_classifier import QueryClassifier
from app.services.context_strategy import ContextStrategyEngine
from app.services.intent_service import IntentService
from app.repositories.knowledge_search_repository import KnowledgeSearchRepository
from app.services.ranking_service import RankingService
from app.services.compression_service import CompressionService

db = SessionLocal()
_vector_store = QdrantVectorStore()
_embedder = EmbeddingService()

# TEST QUERY 1: 'Whose resume is this?' on KB 1 (resume)
query = "Whose resume is this?"
workspace_id = 1
kb_id = 1

print(f"=== RETRIEVAL TRACE FOR KB_ID={kb_id} (resume) ===")

# 1. Classification
classification = QueryClassifier.classify(query)
category = classification["category"]
strategy = ContextStrategyEngine.determine_strategy(category)
print(f"1. Classification: Category='{category}' | Strategy='{strategy}'")

# 2. Hybrid Search
expanded_terms = IntentService.expand_query(query)
search_query = " ".join(expanded_terms)
print(f"2. Expanded Search Query: '{search_query}'")
raw_hits = HybridSearchService.search(
    db=db,
    query=search_query,
    workspace_id=workspace_id,
    knowledge_base_id=[kb_id],
    vector_weight=0.7,
    keyword_weight=0.3,
    top_k=20,
    threshold=0.1
)
print(f"3. Raw Hits from Hybrid Search: {len(raw_hits)}")
for idx, hit in enumerate(raw_hits):
    print(f"   Hit {idx+1}: Chunk ID {hit['chunk_id']} | Score: {hit['score']:.4f} | Text: {hit['text'][:100]}...")

# 4. Near-Duplicate Chunk Filtering
unique_hits = []
duplicate_threshold = 0.90
from app.utils.similarity import compute_jaccard_similarity
for hit in raw_hits:
    is_duplicate = False
    for existing in unique_hits:
        sim = compute_jaccard_similarity(hit["text"], existing["text"])
        if sim >= duplicate_threshold:
            is_duplicate = True
            break
    if not is_duplicate:
        unique_hits.append(hit)
print(f"4. Unique Hits (after Jaccard deduplication): {len(unique_hits)}")

# 5. Fetch document metadata
if unique_hits:
    doc_ids = {hit["document_id"] for hit in unique_hits}
    doc_metadata = KnowledgeSearchRepository.get_bulk_document_metadata(db, list(doc_ids))
    print(f"5. Document IDs: {doc_ids} | Metadata: {list(doc_metadata.keys())}")

    # 6. Reranking
    ranked_hits = RankingService.rerank(
        chunks=unique_hits,
        doc_metadata=doc_metadata,
        max_context_tokens=4000 * 2,
        enable_reranking=settings.ENABLE_RERANKING
    )
    print(f"6. Ranked Chunks count: {len(ranked_hits)}")
    for idx, h in enumerate(ranked_hits):
        print(f"   Rank {idx+1}: Chunk ID {h.get('chunk_id')} | Score: {h.get('score')} | Composite Score: {h.get('composite_score')}")

    # 7. Source Diversity Filter (Max 2 chunks from same doc)
    diverse_hits = []
    doc_count = {}
    for hit in ranked_hits:
        doc_id = hit["document_id"]
        count = doc_count.get(doc_id, 0)
        if count < 2:
            diverse_hits.append(hit)
            doc_count[doc_id] = count + 1
    print(f"7. Diverse Hits count: {len(diverse_hits)}")

    # 8. Context Compression
    compressed_hits = CompressionService.compress_chunks(diverse_hits, max_tokens=4000)
    print(f"8. Compressed Hits count: {len(compressed_hits)}")

    # 9. Token Budget Trimming
    final_hits = RankingService._apply_token_budget(compressed_hits, 4000)
    print(f"9. Final Hits count: {len(final_hits)}")
else:
    print("No hits to rank.")

db.close()
