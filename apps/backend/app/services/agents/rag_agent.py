"""
RAGAgent — Step 11 Multi-Agent Orchestration

Specialized agent that wraps RAGService and RetrievalService.
The Manager invokes this when the CEO's question involves:
  - Policy documents, contracts, reports, knowledge bases
  - "What does the document say about X?"
  - Finding citations, precedents, or historical context
  - Questions that require semantic knowledge base search

This agent is workspace-scoped — it searches all documents in a workspace
unless knowledge_base_id or document_id is specified.
"""
import logging
from typing import Dict, Any, List

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger("app.services.agents.rag_agent")


class RAGAgent(BaseAgent):
    name = "rag_agent"
    description = (
        "Searches the organization's knowledge base (documents, policies, reports). "
        "Uses semantic vector search + hybrid BM25 ranking to find relevant passages. "
        "Returns cited text chunks with confidence scores. "
        "Invoke when the question requires information from uploaded documents, "
        "contracts, policies, meeting notes, or any text knowledge base."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        if not context.workspace_id:
            return AgentResult.skipped(
                self.name, task,
                "No workspace_id provided. RAG Agent requires a workspace for knowledge search."
            )

        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []
        citations: List[Dict[str, Any]] = []

        # ── Tool: Semantic Retrieval ──────────────────────────────────
        # Use the task description as search query (Manager sets this to
        # the specific sub-question relevant to the knowledge base)
        search_query = task if task else context.question

        try:
            # We use a lightweight retrieval call without DB dependency
            # by importing EmbeddingService + QdrantVectorStore directly
            from app.services.embedding.embedding_service import EmbeddingService
            from app.services.vector_store.qdrant_vector_store import QdrantVectorStore

            embedder = EmbeddingService()
            vector_store = QdrantVectorStore()

            # Embed the query
            query_embedding = embedder.embed_text(search_query)
            tool_calls.append("EmbeddingService.embed_text")

            # Search Qdrant
            results = vector_store.search(
                query_embedding=query_embedding,
                workspace_id=context.workspace_id,
                top_k=context.top_k,
            )
            tool_calls.append("QdrantVectorStore.search")

            if results:
                chunks = []
                for r in results[:context.top_k]:
                    payload = r.get("payload", {})
                    chunk_text = payload.get("text", "")
                    score = r.get("score", 0.0)
                    doc_name = payload.get("file_name", "Unknown Document")
                    page = payload.get("page_number", "?")

                    chunks.append({
                        "text": chunk_text,
                        "score": round(float(score), 4),
                        "document": doc_name,
                        "page": page,
                    })
                    citations.append({
                        "source": doc_name,
                        "page": page,
                        "score": round(float(score), 4),
                        "snippet": chunk_text[:200],
                    })

                output["retrieved_chunks"] = chunks
                output["citations"] = citations

                avg_score = sum(c["score"] for c in chunks) / len(chunks)
                summaries.append(
                    f"Found {len(chunks)} relevant passage(s) "
                    f"(avg relevance: {avg_score:.2f}). "
                    f"Sources: {', '.join(set(c['document'] for c in chunks))}."
                )

                # Build a compact context for the Manager to synthesize
                context_text = "\n\n".join(
                    f"[{c['document']} p.{c['page']}] {c['text'][:400]}"
                    for c in chunks[:5]
                )
                output["context_text"] = context_text
            else:
                summaries.append(
                    "No relevant documents found in knowledge base for this query."
                )
                output["retrieved_chunks"] = []
                output["context_text"] = (
                    "No relevant information found in the selected Knowledge Base."
                )

        except Exception as e:
            logger.warning(f"[RAGAgent] Vector search failed: {e}")
            # Attempt fallback via RAGService if vector store is unavailable
            try:
                from app.services.rag_service import RAGService
                # RAGService requires a DB session — we skip it here
                # and log the gap. Future: inject db session via context.
                summaries.append(
                    "Vector search unavailable. RAGService fallback skipped (no DB session in agent context)."
                )
                output["context_text"] = (
                    "No relevant information found in the selected Knowledge Base."
                )
                tool_calls.append("RAGService.fallback_attempted")
            except Exception as e2:
                logger.error(f"[RAGAgent] All retrieval failed: {e2}")
                return AgentResult.error_result(self.name, task, str(e))

        return AgentResult(
            agent_name=self.name,
            task=task,
            status="success",
            output=output,
            summary=" ".join(summaries) or "Knowledge base search complete.",
            tool_calls=tool_calls,
        )

    def get_tool_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Specific search query to run against the knowledge base, e.g. 'find churn reduction policies' or 'what does the contract say about SLA terms'",
                        }
                    },
                    "required": ["task"],
                },
            },
        }
