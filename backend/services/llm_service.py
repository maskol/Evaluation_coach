"""
LLM Service for AI coaching responses
Integrates with LangChain and OpenAI
"""

import json
import os
from typing import Any, Dict, Optional, List, Tuple

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from .prompt_service import PromptService

# Load environment variables
load_dotenv()

# Check if OpenAI API key is available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI = OPENAI_API_KEY is not None and OPENAI_API_KEY.strip() != ""

if USE_OPENAI:
    try:
        from openai import OpenAI

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        USE_OPENAI = False
        openai_client = None
else:
    openai_client = None

# Check for Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_client = None
try:
    from openai import OpenAI

    # Ollama has OpenAI-compatible API
    ollama_client = OpenAI(
        base_url=f"{OLLAMA_BASE_URL}/v1", api_key="ollama"
    )  # Ollama doesn't need real API key
except Exception:
    pass


class LLMService:
    """Service for LLM-based coaching and analysis"""

    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.use_openai = USE_OPENAI
        self.client = openai_client
        self.ollama_client = ollama_client
        self.ollama_base_url = OLLAMA_BASE_URL
        self._knowledge_cache: Optional[str] = None
        self.prompt_service = PromptService()

    def _format_retrieved_docs(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Format retrieved RAG documents for LLM context."""
        if not retrieved_docs:
            return "(No relevant knowledge base documents retrieved)"

        formatted = []
        for i, doc in enumerate(retrieved_docs[:5], 1):  # Limit to top 5
            source = doc.get("metadata", {}).get("source", "unknown")
            content = doc.get("content", "")
            score = doc.get("similarity_score", 0)
            # Truncate long content
            if len(content) > 400:
                content = content[:400] + "..."
            formatted.append(f"[{i}] {source} (relevance: {score:.2f}):\n{content}")

        return "\n\n".join(formatted)

    def _is_ollama_model(self, model: str) -> bool:
        """Check if the model is an Ollama model"""
        ollama_prefixes = [
            "llama",
            "mistral",
            "ministral",
            "codellama",
            "phi",
            "gemma",
            "qwen",
            "deepseek",
        ]
        return any(model.lower().startswith(prefix) for prefix in ollama_prefixes)

    def _get_client(self, model: str = None):
        """Get the appropriate client based on model"""
        model_to_use = model or self.model
        if self._is_ollama_model(model_to_use):
            return self.ollama_client
        return self.client

    def _has_llm_client(self, model: Optional[str] = None) -> Tuple[bool, str]:
        model_to_use = model or self.model
        client = self._get_client(model_to_use)
        if client is None:
            return (
                False,
                "No LLM client available. Configure OPENAI_API_KEY for OpenAI models, or select an Ollama model and ensure Ollama is running.",
            )
        if self._is_ollama_model(model_to_use) and self.ollama_client is None:
            return (
                False,
                "Ollama client is not available. Ensure the 'openai' Python package is installed and OLLAMA_BASE_URL is reachable.",
            )
        if (not self._is_ollama_model(model_to_use)) and (not self.use_openai):
            return (
                False,
                "OpenAI API key is not configured (OPENAI_API_KEY missing).",
            )
        return True, ""

    def _compact_metrics_facts(self, facts: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce large metric payloads into a small, LLM-friendly snapshot."""
        compact: Dict[str, Any] = {}

        # Strategic targets
        targets = facts.get("strategic_targets") if isinstance(facts, dict) else None
        if isinstance(targets, dict):
            compact["strategic_targets"] = {
                k: targets.get(k)
                for k in [
                    "leadtime_target_2026",
                    "leadtime_target_2027",
                    "leadtime_target_true_north",
                    "planning_accuracy_target_2026",
                    "planning_accuracy_target_2027",
                    "planning_accuracy_target_true_north",
                ]
            }

        # Lead time snapshot
        leadtime = facts.get("leadtime") if isinstance(facts, dict) else None
        if isinstance(leadtime, dict):
            stage_stats = leadtime.get("stage_statistics") or {}
            total = stage_stats.get("total_leadtime") or {}
            if isinstance(total, dict):
                compact["leadtime_total"] = {
                    "mean_days": total.get("mean"),
                    "median_days": total.get("median"),
                    "p85_days": total.get("p85"),
                    "p95_days": total.get("p95"),
                    "count": total.get("count"),
                }

        # Planning snapshot
        planning = facts.get("planning") if isinstance(facts, dict) else None
        if isinstance(planning, dict):
            compact["planning"] = {
                "overall_accuracy": planning.get("overall_accuracy")
                or planning.get("accuracy_percentage")
                or planning.get("planning_accuracy"),
                "predictability_score": planning.get("predictability_score"),
            }

        # Throughput snapshot
        throughput = facts.get("throughput") if isinstance(facts, dict) else None
        if isinstance(throughput, dict):
            compact["throughput"] = {
                "features_delivered": throughput.get("features_delivered")
                or throughput.get("delivered_features")
                or throughput.get("throughput"),
                "trend": throughput.get("trend"),
            }

        # Bottlenecks (top 3)
        bottlenecks = facts.get("bottlenecks") if isinstance(facts, dict) else None
        if isinstance(bottlenecks, dict):
            items = bottlenecks.get("bottlenecks")
            if isinstance(items, list):
                compact["bottlenecks_top"] = [
                    {
                        "stage": b.get("stage") or b.get("name"),
                        "mean_days": b.get("mean") or b.get("avg") or b.get("avg_days"),
                        "median_days": b.get("median"),
                        "p85_days": b.get("p85"),
                        "count": b.get("count"),
                    }
                    for b in items[:3]
                    if isinstance(b, dict)
                ]

        # Recent insights (titles only + severity)
        recent = facts.get("recent_insights") if isinstance(facts, dict) else None
        if isinstance(recent, list):
            compact["recent_insights"] = [
                {
                    "title": i.get("title"),
                    "severity": i.get("severity"),
                    "confidence": i.get("confidence"),
                }
                for i in recent
                if isinstance(i, dict)
            ]

        return compact

    def _build_system_prompt(
        self, retrieved_docs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build system prompt with query-relevant RAG knowledge."""
        knowledge = self._format_retrieved_docs(retrieved_docs or [])

        # Get prompt from prompt service
        base_prompt = self.prompt_service.get_active_prompt("coach_system")

        # Fallback to hardcoded if not found
        if not base_prompt:
            maturity_model = """
SAFe BUSINESS AGILITY MATURITY (use as benchmark):
Level 1 - Initial: Ad-hoc processes, reactive, siloed teams
Level 2 - Managed: Basic Scrum/Kanban, some flow metrics tracked
Level 3 - Defined: SAFe adopted, ARTs coordinated, PI Planning regular
Level 4 - Quantitatively Managed: Data-driven decisions, predictable delivery, flow optimization
Level 5 - Optimizing: Continuous improvement culture, strategic agility, world-class metrics
"""
            base_prompt = (
                "You are an elite Agile strategy expert and SAFe transformation coach with 15+ years of experience coaching Fortune 500 companies. "
                "You have deep expertise in flow metrics, Lean principles, Product Operating Models, and organizational transformation.\n\n"
                "YOUR COACHING PERSONAS:\n"
                "- Strategic Advisor: Guide long-term vision, portfolio strategy, and organizational design.\n"
                "- Tactical Coach: Help teams improve daily flow, reduce bottlenecks, and run experiments.\n"
                "- Challenger: Ask tough questions that expose assumptions, tradeoffs, and root causes.\n\n"
                "YOUR MISSION:\n"
                "1. Interpret provided metrics/insights without inventing data.\n"
                "2. Propose 2-4 concrete, testable experiments/actions.\n"
                "3. Ask 1-3 challenging questions that provoke reflection.\n"
                "4. Suggest the next best step in this app (e.g., switch scope, generate insights, check metrics).\n"
                "5. Reference SAFe/Lean best practices and maturity benchmarks when relevant.\n\n"
                "OUTPUT FORMAT (HTML only, no Markdown):\n"
                "- Start with a 2-3 sentence assessment\n"
                "- <strong>Proposed Actions:</strong> <ul><li>...</li></ul>\n"
                "- <strong>Challenging Questions:</strong> <ul><li>...</li></ul>\n"
                "- <strong>Evidence Used:</strong> (cite key numbers you relied on)\n"
                "- <strong>Next Step:</strong> (what to do in this app)\n\n"
                + maturity_model
            )

        return (
            base_prompt
            + "\n\nRELEVANT KNOWLEDGE BASE DOCUMENTS (retrieved via semantic search):\n"
            + knowledge
        )

    async def generate_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        facts: Optional[Dict[str, Any]],
        session_id: Optional[str],
        db: Session,
    ) -> str:
        """
        Generate AI coach response based on user message and context

        Args:
            message: User's question/message
            context: Current analysis context (scope, time range, etc.)
            db: Database session for fetching relevant data

        Returns:
            AI-generated response
        """

        # LLM-first coaching. Fall back to rule-based responses when no LLM is configured.
        ok, reason = self._has_llm_client(self.model)
        if not ok:
            # Keep the old keyword behavior, but make it explicit how to enable the real coach.
            message_lower = message.lower()
            if "wip" in message_lower or "work in progress" in message_lower:
                base = self._generate_wip_response(context)
            elif "flow" in message_lower or "efficiency" in message_lower:
                base = self._generate_flow_response(context)
            elif "quality" in message_lower or "defect" in message_lower:
                base = self._generate_quality_response(context)
            elif "team" in message_lower or "stability" in message_lower:
                base = self._generate_team_response(context)
            elif "scorecard" in message_lower or "health" in message_lower:
                base = self._generate_scorecard_response(context)
            elif "improve" in message_lower or "recommendation" in message_lower:
                base = self._generate_improvement_response(context)
            else:
                base = self._generate_default_response()

            return (
                base
                + "<br><br><strong>Note:</strong> The full AI Coach requires an LLM connection. "
                + f"Current model: <strong>{self.model}</strong> | Temp: <strong>{self.temperature}</strong><br>"
                + f"Why it’s not using the LLM: {reason}<br>"
                + "To enable: set <strong>OPENAI_API_KEY</strong> for OpenAI models, or choose an Ollama model (e.g., llama*, mistral*, qwen*) and run Ollama."
            )

        # Pull recent chat history for continuity
        history_msgs: List[Dict[str, str]] = []
        if session_id:
            try:
                from database import ChatMessage

                rows = (
                    db.query(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(12)
                    .all()
                )
                for row in reversed(rows):
                    role = "assistant" if row.role == "assistant" else "user"
                    history_msgs.append({"role": role, "content": row.content})
            except Exception:
                history_msgs = []

        compact_facts = self._compact_metrics_facts(facts or {})

        # Retrieve relevant knowledge using RAG based on user query
        retrieved_docs: List[Dict[str, Any]] = []
        try:
            from backend.services.rag_service import get_rag_service

            rag = get_rag_service()
            retrieved_docs = rag.retrieve(message, top_k=5)
        except Exception as e:
            print(f"⚠️ RAG retrieval failed: {e}")
            # Continue without RAG knowledge

        context_obj = context or {}
        user_prompt = (
            "User message:\n"
            + message.strip()
            + "\n\nContext (scope/time range/focus):\n"
            + json.dumps(context_obj, ensure_ascii=False)
            + "\n\nGrounding facts (do not invent beyond these):\n"
            + json.dumps(compact_facts, ensure_ascii=False)
            + "\n\nRespond as an Agile strategy coach."
        )

        try:
            client = self._get_client(self.model)
            messages: List[Dict[str, str]] = [
                {
                    "role": "system",
                    "content": self._build_system_prompt(retrieved_docs),
                },
            ]
            # Add prior conversation (already stored as HTML; that's ok)
            messages.extend(history_msgs)
            messages.append({"role": "user", "content": user_prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=650,  # Increased for structured expert responses
            )
            content = response.choices[0].message.content
            result = (content or "").strip()
            if not result:
                return self._generate_default_response()
            # Ensure response has structure; if LLM omitted sections, add a note
            if "Evidence Used:" not in result:
                result += "<br><br><strong>Evidence Used:</strong> (Response based on provided metrics)"
            return result
        except Exception as e:
            # If LLM call fails at runtime, fall back gracefully.
            return (
                self._generate_default_response()
                + "<br><br><strong>Note:</strong> LLM call failed at runtime. "
                + f"Error: {str(e)}"
            )

    def _generate_wip_response(self, context: Optional[Dict]) -> str:
        return """📊 <strong>Work in Progress Analysis</strong><br><br>
            Current WIP across your scope:<br>
            • Average WIP ratio: 1.3x team size<br>
            • Target: ≤1.5x<br>
            • Status: <span style="color: #34C759;">✓ Healthy</span><br><br>
            However, Customer Experience ART shows 2.3x ratio, which requires attention. 
            Would you like me to generate specific recommendations for this ART?"""

    def _generate_flow_response(self, context: Optional[Dict]) -> str:
        return """📈 <strong>Flow Efficiency Insights</strong><br><br>
            Your current flow efficiency: <strong>67%</strong><br>
            • Industry average: 15%<br>
            • High performer benchmark: 40%<br>
            • Your status: <span style="color: #34C759;">✓ Excellent!</span><br><br>
            You're significantly above high performer benchmarks. Main drivers:<br>
            • Reduced blocked time (28% decrease)<br>
            • Better dependency management<br>
            • Cross-team collaboration improvements<br><br>
            Platform Engineering ART is leading at 72%. Want to see their best practices?"""

    def _generate_quality_response(self, context: Optional[Dict]) -> str:
        return """✅ <strong>Quality Metrics Overview</strong><br><br>
            Defect Escape Rate: <strong>4.2%</strong><br>
            • Target: <5%<br>
            • Status: <span style="color: #34C759;">✓ Acceptable</span><br><br>
            <span style="color: #FF9500;">⚠️ Warning:</span> Mobile Apps team at 7.2% with 68% stories lacking test coverage.<br><br>
            Recommendations:<br>
            1. Implement Definition of Done checklist<br>
            2. Set 80% test coverage target<br>
            3. Add automated testing pipeline<br><br>
            Would you like detailed analysis for Mobile Apps team?"""

    def _generate_team_response(self, context: Optional[Dict]) -> str:
        return """👥 <strong>Team Stability Analysis</strong><br><br>
            Overall team stability: <strong>89%</strong><br>
            • Industry target: >85%<br>
            • Status: <span style="color: #34C759;">✓ Excellent</span><br><br>
            All ARTs show stable team composition with minimal turnover. 
            This is a key enabler for your strong flow efficiency results.<br><br>
            Want to see team-specific breakdowns?"""

    def _generate_scorecard_response(self, context: Optional[Dict]) -> str:
        return """📋 <strong>Health Scorecard Request</strong><br><br>
            I can generate a comprehensive scorecard for:<br>
            • Portfolio (all ARTs)<br>
            • Specific ART<br>
            • Individual Team<br><br>
            Your current context: <strong>Portfolio</strong><br><br>
            Use the <strong>"Generate Scorecard"</strong> button in the sidebar, or tell me which scope you'd like to analyze!"""

    def _generate_improvement_response(self, context: Optional[Dict]) -> str:
        return """💡 <strong>Improvement Recommendations</strong><br><br>
            Based on your current metrics, top 3 priorities:<br><br>
            <strong>1. Address High WIP (Critical)</strong><br>
            Customer Experience ART needs immediate WIP limit enforcement.<br><br>
            <strong>2. Improve Test Coverage (Warning)</strong><br>
            Mobile Apps team requires testing discipline improvements.<br><br>
            <strong>3. Scale Best Practices (Opportunity)</strong><br>
            Platform Engineering's success patterns can be shared across ARTs.<br><br>
            Click <strong>"Generate Insights"</strong> for detailed action plans!"""

    def _generate_default_response(self) -> str:
        return """🤔 <strong>I can help you with:</strong><br><br>
            • <strong>Metrics analysis</strong> - Ask about flow, quality, predictability, or WIP<br>
            • <strong>Scorecards</strong> - Generate health assessments for Portfolio/ART/Team<br>
            • <strong>Insights</strong> - Get evidence-based recommendations<br>
            • <strong>Trends</strong> - Understand changes over time<br>
            • <strong>Best practices</strong> - Learn from high-performing teams<br><br>
            Try asking: "What's our flow efficiency?" or "Show me quality metrics" """

    def enhance_insight_with_expert_analysis(
        self,
        insight_title: str,
        observation: str,
        interpretation: str,
        metrics: Dict[str, Any],
        root_causes: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
    ) -> str:
        """
        Enhance insight with expert agile coach analysis using LLM

        Returns expert commentary as a string
        """
        if not self.use_openai:
            # Return a default expert perspective without LLM
            return self._generate_fallback_expert_commentary(insight_title)

        try:
            # Build context for the LLM
            metrics_str = "\n".join([f"- {k}: {v}" for k, v in metrics.items()])
            root_causes_str = "\n".join(
                [f"- {rc.get('description', 'N/A')}" for rc in root_causes]
            )
            recommendations_str = "\n".join(
                [
                    f"- {rec.get('action', 'N/A')} (Expected: {rec.get('expected_outcome', 'N/A')})"
                    for rec in recommendations
                ]
            )

            # Get prompts from prompt service
            analysis_prompt_template = self.prompt_service.get_active_prompt(
                "insight_analysis"
            )
            system_prompt = self.prompt_service.get_active_prompt("insight_system")

            # Fallback to hardcoded if not found
            if not analysis_prompt_template:
                analysis_prompt_template = """You are an expert Agile Coach and SAFe consultant with 15+ years of experience coaching Fortune 500 companies. You have deep expertise in flow metrics, lean principles, and organizational transformation.

INSIGHT ANALYSIS:
Title: {insight_title}

Observation: {observation}

Interpretation: {interpretation}

Key Metrics:
{metrics_str}

Root Causes Identified:
{root_causes_str}

Recommended Actions:
{recommendations_str}

As an experienced agile coach, provide a brief (2-3 sentences) expert commentary that:
1. Validates or adds context to the findings from your industry experience
2. Highlights the most critical aspect teams often overlook
3. Provides encouragement or urgency as appropriate

Keep it conversational, actionable, and grounded in real-world experience. Do not repeat the observation or recommendations - add NEW insights from your expertise."""

            if not system_prompt:
                system_prompt = "You are an expert Agile Coach and SAFe consultant with extensive experience in enterprise agile transformations. You provide practical, experience-based guidance."

            prompt = analysis_prompt_template.format(
                insight_title=insight_title,
                observation=observation,
                interpretation=interpretation,
                metrics_str=metrics_str,
                root_causes_str=root_causes_str,
                recommendations_str=recommendations_str,
            )

            client = self._get_client(self.model)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=200,
            )

            expert_commentary = response.choices[0].message.content.strip()
            return expert_commentary

        except Exception as e:
            print(f"⚠️ LLM expert analysis failed: {e}")
            return self._generate_fallback_expert_commentary(insight_title)

    def _generate_fallback_expert_commentary(self, insight_title: str) -> str:
        """Generate rule-based expert commentary when LLM is unavailable"""
        commentaries = {
            "bottleneck": "From my experience, bottlenecks like this typically indicate systemic process issues rather than individual team problems. Focus on flow optimization and limit WIP before adding more resources. Quick wins often come from better handoffs and reducing batch sizes.",
            "waste": "Waiting time is the silent killer of delivery performance. In my consulting work, teams that address waiting waste see 40-60% improvements in lead time within 2 PIs. The key is making the invisible visible through value stream mapping.",
            "predictability": "Low PI Predictability usually stems from optimistic planning rather than execution issues. High-performing organizations I've coached maintain 15-20% capacity buffers and ruthlessly protect committed work. Trust is built through consistent delivery.",
            "flow efficiency": "Flow efficiency below 30% is common but not acceptable. Elite teams operate at 40%+ by maintaining strict WIP limits and focusing on finishing over starting. This is where the real transformation happens.",
            "variability": "High variability destroys predictability and stakeholder confidence. In successful transformations, teams that implement consistent sizing practices and swarm on outliers see dramatic improvements in 2-3 PIs. Small batches are your friend.",
            "throughput": "Declining throughput often signals accumulated technical debt or increasing complexity. Smart teams allocate 20-30% of capacity to technical excellence and refactoring. This is an investment, not a cost.",
        }

        # Match insight type
        title_lower = insight_title.lower()
        for key, commentary in commentaries.items():
            if key in title_lower:
                return commentary

        return "In my experience working with high-performing organizations, addressing issues like this systematically leads to sustainable improvements. Focus on the fundamentals: limit WIP, reduce batch size, and make work visible."
