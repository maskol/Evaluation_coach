"""PI Report Generation Service

Generates comprehensive Program Increment reports for management,
comparing performance vs targets and providing actionable proposals.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


class PIReportService:
    """Service for generating PI management reports"""

    def __init__(self, llm_service, leadtime_service=None, rag_service=None):
        self.llm_service = llm_service
        self.leadtime_service = leadtime_service
        self.rag_service = rag_service

    def get_previous_pi(self, pi: str) -> str:
        """Calculate the previous PI name

        Args:
            pi: Current PI (e.g., "25Q4")

        Returns:
            Previous PI name (e.g., "25Q3")
        """
        try:
            year = pi[:2]
            quarter = pi[2:]
            q_num = int(quarter[1])

            if q_num > 1:
                return f"{year}Q{q_num - 1}"
            else:
                return f"{int(year) - 1}Q4"
        except:
            return None

    def calculate_metrics(
        self,
        features: List[Dict],
        pip_features: List[Dict],
        throughput_features: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate metrics from feature data

        Args:
            features: Flow leadtime features
            pip_features: PIP planning features
            throughput_features: Throughput data

        Returns:
            Dictionary of calculated metrics
        """
        metrics = {}

        # Flow efficiency and lead-time from features
        if features:
            value_add_times = []
            total_times = []

            for f in features:
                value_add = f.get("in_progress", 0) + f.get("in_reviewing", 0)
                total = f.get("total_leadtime", 0)

                if total > 0:
                    value_add_times.append(value_add)
                    total_times.append(total)

            if value_add_times and total_times:
                avg_value_add = sum(value_add_times) / len(value_add_times)
                avg_total = sum(total_times) / len(total_times)
                metrics["flow_efficiency"] = (
                    round((avg_value_add / avg_total) * 100, 1) if avg_total > 0 else 0
                )
                metrics["avg_leadtime"] = round(avg_total, 1)

        # Planning accuracy from PIP data
        if pip_features:
            planned = sum(1 for f in pip_features if f.get("planned_committed", 0) > 0)
            delivered = sum(
                1
                for f in pip_features
                if f.get("planned_committed", 0) > 0
                and f.get("plc_delivery") not in ["", "0", None, "null"]
            )

            if planned > 0:
                metrics["planning_accuracy"] = round((delivered / planned) * 100, 1)

        # Throughput
        metrics["throughput"] = len(throughput_features) if throughput_features else 0

        return metrics

    def generate_report_prompt(
        self,
        pi: str,
        current_metrics: Dict[str, Any],
        previous_metrics: Optional[Dict[str, Any]],
        targets: Dict[str, Any],
        rag_context: Optional[List[str]] = None,
    ) -> str:
        """Generate the LLM prompt for PI report

        Args:
            pi: PI being analyzed
            current_metrics: Current PI metrics
            previous_metrics: Previous PI metrics (if available)
            targets: Strategic targets
            rag_context: RAG knowledge base context

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert Agile & SAFe coach preparing a comprehensive Program Increment (PI) performance report for senior management.

**PI Being Analyzed:** {pi}

**Current PI Performance:**
- Flow Efficiency: {current_metrics.get('flow_efficiency', 'N/A')}%
- Average Lead-Time: {current_metrics.get('avg_leadtime', 'N/A')} days
- Planning Accuracy: {current_metrics.get('planning_accuracy', 'N/A')}%
- Features Delivered: {current_metrics.get('throughput', 'N/A')}
"""

        # Add comparison with previous PI
        if previous_metrics:
            flow_change = current_metrics.get(
                "flow_efficiency", 0
            ) - previous_metrics.get("flow_efficiency", 0)
            leadtime_change = current_metrics.get(
                "avg_leadtime", 0
            ) - previous_metrics.get("avg_leadtime", 0)
            planning_change = current_metrics.get(
                "planning_accuracy", 0
            ) - previous_metrics.get("planning_accuracy", 0)
            throughput_change = current_metrics.get(
                "throughput", 0
            ) - previous_metrics.get("throughput", 0)

            prompt += f"""
**Previous PI ({previous_metrics.get('pi_name')}) Performance:**
- Flow Efficiency: {previous_metrics.get('flow_efficiency', 'N/A')}%
- Average Lead-Time: {previous_metrics.get('avg_leadtime', 'N/A')} days
- Planning Accuracy: {previous_metrics.get('planning_accuracy', 'N/A')}%
- Features Delivered: {previous_metrics.get('throughput', 'N/A')}

**Changes from Previous PI:**
- Flow Efficiency: {flow_change:+.1f}% ({'improved' if flow_change > 0 else 'declined'})
- Average Lead-Time: {leadtime_change:+.1f} days ({'improved' if leadtime_change < 0 else 'increased'})
- Planning Accuracy: {planning_change:+.1f}% ({'improved' if planning_change > 0 else 'declined'})
- Throughput: {throughput_change:+d} features ({'increased' if throughput_change > 0 else 'decreased'})
"""

        # Add strategic targets
        if targets:
            prompt += "\n**Strategic Targets:**\n"
            for metric_name, target_obj in targets.items():
                prompt += f"- {metric_name}: 2026 = {target_obj.target_2026}, 2027 = {target_obj.target_2027}, True North = {target_obj.true_north}\n"

        # Add RAG context
        if rag_context:
            prompt += "\n**Knowledge Base Context:**\n"
            for i, doc in enumerate(rag_context[:3], 1):
                prompt += f"\n{i}. {doc}\n"

        prompt += """

**Please generate a comprehensive management report with the following sections:**

1. **Executive Summary** (2-3 paragraphs)
   - Overall PI performance assessment
   - Key achievements and concerns  
   - Bottom-line impact on strategic goals

2. **Performance vs Targets**
   - Compare each metric against strategic targets
   - Highlight gaps and achievements
   - Trend analysis (are we on track?)

3. **Improvements from Previous PI**
   - What improved and why
   - What declined and root causes
   - Key lessons learned

4. **Detailed Analysis**
   - Flow Efficiency deep-dive
   - Lead-Time analysis
   - Planning Accuracy assessment
   - Throughput evaluation

5. **Root Causes & Systemic Issues**
   - Identify underlying problems
   - Distinguish symptoms from causes
   - Connect issues to organizational practices

6. **Actionable Proposals**
   - Specific, prioritized recommendations
   - Short-term (next sprint) actions
   - Medium-term (next PI) initiatives
   - Long-term (2-3 PIs) strategic changes
   - For each: owner, effort, success criteria

7. **Path to Target Achievement**
   - Realistic timeline to reach 2026/2027 targets
   - Required improvements per PI
   - Key dependencies and risks
   - Recommended focus areas

**Format:** Use clear markdown with headers (##, ###), bullet points, and **bold** text for emphasis. Be data-driven but also provide strategic insights. This report will be presented to executive leadership.
"""

        return prompt


# Create singleton instance
pi_report_service = None


def get_pi_report_service(llm_service, leadtime_service=None, rag_service=None):
    """Get or create PI report service instance"""
    global pi_report_service
    if pi_report_service is None:
        pi_report_service = PIReportService(llm_service, leadtime_service, rag_service)
    return pi_report_service
