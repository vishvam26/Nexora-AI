import logging
from typing import Dict, List, Set, Any
from sqlalchemy.orm import Session
from app.models.knowledge_graph import KnowledgeNode, KnowledgeEdge

logger = logging.getLogger("app.services.knowledge_graph_service")


class KnowledgeGraphService:
    """
    Module 4 & 5: Knowledge Graph Service
    Manages Graph edges, nodes, entity extraction, and query-expansion relationships.
    """

    @staticmethod
    def extract_entities_from_text(db: Session, workspace_id: int, document_id: int, text: str) -> List[KnowledgeNode]:
        """
        Parses text to extract standard technical entities and stores them.
        """
        # Dictionary of tech terms to match
        ENTITY_RULES = {
            "Language": ["python", "javascript", "typescript", "golang", "rust", "cpp", "java", "ruby"],
            "Framework": ["fastapi", "django", "flask", "nextjs", "react", "vue", "angular", "express"],
            "Database": ["postgresql", "sqlite", "mongodb", "redis", "mysql", "dynamodb", "supabase"],
            "Concept": ["jwt", "oauth", "authentication", "authorization", "token", "session", "docker"],
        }

        nodes = []
        text_lower = text.lower()

        # Extract matches
        for entity_type, keywords in ENTITY_RULES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Check if already exists in graph node list for document
                    existing = db.query(KnowledgeNode).filter(
                        KnowledgeNode.workspace_id == workspace_id,
                        KnowledgeNode.name == keyword,
                        KnowledgeNode.document_id == document_id,
                    ).first()

                    if not existing:
                        node = KnowledgeNode(
                            workspace_id=workspace_id,
                            name=keyword,
                            entity_type=entity_type,
                            document_id=document_id
                        )
                        db.add(node)
                        nodes.append(node)

        db.commit()

        # Connect entities found together in this document
        if len(nodes) > 1:
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    edge = KnowledgeEdge(
                        workspace_id=workspace_id,
                        source_node_id=nodes[i].id,
                        target_node_id=nodes[j].id,
                        relation_type="RELATED_TO",
                        weight=1.0
                    )
                    db.add(edge)
            db.commit()

        return nodes

    @staticmethod
    def get_related_concepts(db: Session, workspace_id: int, seed_terms: List[str], max_depth: int = 2) -> Set[str]:
        """
        Traverses nodes and edges to find connected related entity concepts.
        """
        if not seed_terms:
            return set()

        related = set()
        queue = [(term.lower(), 0) for term in seed_terms]
        visited = set()

        while queue:
            term, depth = queue.pop(0)
            if term in visited or depth > max_depth:
                continue
            visited.add(term)

            # Find matching node
            node = db.query(KnowledgeNode).filter(
                KnowledgeNode.workspace_id == workspace_id,
                KnowledgeNode.name == term
            ).first()

            if node:
                # Find connected edges
                edges = db.query(KnowledgeEdge).filter(
                    KnowledgeEdge.workspace_id == workspace_id,
                    (KnowledgeEdge.source_node_id == node.id) | (KnowledgeEdge.target_node_id == node.id)
                ).all()

                for edge in edges:
                    other_id = edge.target_node_id if edge.source_node_id == node.id else edge.source_node_id
                    other_node = db.query(KnowledgeNode).filter(KnowledgeNode.id == other_id).first()
                    if other_node:
                        related.add(other_node.name)
                        queue.append((other_node.name, depth + 1))

        return related - set(seed_terms)
