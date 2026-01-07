"""Knowledge Retriever Node (Node 4)"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from ..state import AgentState
from services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


def _generate_retrieval_queries(state: AgentState) -> List[str]:
    """Generate search queries based on agent state and context."""
    queries = []

    # Base query on scope
    if state.get("scope") == "portfolio":
        queries.append("portfolio management best practices strategic themes")
    elif state.get("scope") == "art":
        queries.append("agile release train coordination PI planning")
    elif state.get("scope") == "team":
        queries.append("team agile practices sprint planning story writing")

    # Add queries based on detected patterns or issues
    if state.get("patterns"):
        for pattern in state["patterns"]:
            pattern_type = pattern.get("pattern_type", "")
            if "bottleneck" in pattern_type.lower():
                queries.append("reduce bottlenecks flow efficiency waste reduction")
            elif "lead" in pattern_type.lower() or "time" in pattern_type.lower():
                queries.append("reduce lead time cycle time improvement")
            elif "quality" in pattern_type.lower():
                queries.append("quality built-in test automation definition of done")

    # Add query based on insights
    if state.get("insights"):
        for insight in state["insights"]:
            if insight.get("severity") in ["high", "critical"]:
                title = insight.get("title", "").lower()
                if "epic" in title or "feature" in title:
                    queries.append("epic feature guidelines templates definition")
                elif "business case" in title:
                    queries.append("lean business case economic framework")
                elif "objective" in title:
                    queries.append("PI objectives commitment SMART goals")

    # Default fallback query
    if not queries:
        queries.append("SAFe agile best practices lean principles")

    return queries[:3]  # Limit to top 3 queries


def knowledge_retriever_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Retrieve relevant coaching knowledge using RAG."""
    logger.info(f"Starting knowledge retrieval for {state['scope']}")

    try:
        updates = {"knowledge_retrieval_timestamp": datetime.utcnow()}

        # Get RAG service
        rag = get_rag_service()

        # Generate retrieval queries based on state
        queries = _generate_retrieval_queries(state)
        logger.info(f"Generated {len(queries)} retrieval queries: {queries}")

        # Retrieve relevant documents for each query
        all_retrieved_docs = []
        seen_contents = set()  # Deduplicate chunks

        for query in queries:
            docs = rag.retrieve(query, top_k=3)
            for doc in docs:
                content = doc["content"]
                # Deduplicate by content hash
                if content not in seen_contents:
                    seen_contents.add(content)
                    all_retrieved_docs.append(doc)

        # Store retrieved knowledge in state
        updates["retrieved_knowledge"] = all_retrieved_docs
        updates["retrieval_queries"] = queries

        logger.info(
            f"Knowledge retrieval complete: {len(all_retrieved_docs)} unique documents "
            f"from {len(queries)} queries"
        )
        return updates

    except Exception as e:
        logger.error(f"Error in knowledge retrieval: {e}", exc_info=True)
        return {
            "errors": [f"Knowledge retrieval failed: {str(e)}"],
            "knowledge_retrieval_timestamp": datetime.utcnow(),
            "retrieved_knowledge": [],
        }
