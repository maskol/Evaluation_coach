"""Coaching Node (Node 5)"""

import logging
from datetime import datetime
from typing import Any, Dict

from ..state import AgentState

logger = logging.getLogger(__name__)


def coaching_node(state: AgentState) -> Dict[str, Any]:
    """Node 5: Generate insights and improvement proposals."""
    logger.info("Starting coaching analysis for %s", state["scope"])

    try:
        updates = {"coaching_timestamp": datetime.utcnow()}

        # Consolidate Little's Law insights into main insights list
        littles_law_insights = state.get("littles_law_insights", [])
        if littles_law_insights:
            logger.info(
                "Incorporating %d Little's Law insights", len(littles_law_insights)
            )
            updates["insights"] = littles_law_insights
            updates["reasoning_chain"] = [
                "Applied Little's Law analysis to understand flow dynamics",
                f"Identified {len(littles_law_insights)} actionable insights from flow metrics",
            ]

        # TODO: Implement additional reasoning and coaching logic
        # from backend.coaching.reasoner import Reasoner
        # from backend.coaching.proposal_generator import ProposalGenerator
        # reasoner = Reasoner()
        # insights = reasoner.generate_insights(state)
        # proposals = ProposalGenerator().generate(state, insights)

        logger.info("Coaching analysis complete for %s", state["scope"])
        return updates

    except Exception as e:
        logger.error("Error in coaching: %s", e, exc_info=True)
        return {
            "errors": [f"Coaching failed: {str(e)}"],
            "coaching_timestamp": datetime.utcnow(),
        }
