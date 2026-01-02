"""
LLM Service for AI coaching responses
Integrates with LangChain and OpenAI
"""

import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()


class LLMService:
    """Service for LLM-based coaching and analysis"""

    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

    async def generate_response(
        self, message: str, context: Optional[Dict[str, Any]], db: Session
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

        # For now, return intelligent responses based on keywords
        # TODO: Integrate actual LangChain + OpenAI API

        message_lower = message.lower()

        if "wip" in message_lower or "work in progress" in message_lower:
            return self._generate_wip_response(context)
        elif "flow" in message_lower or "efficiency" in message_lower:
            return self._generate_flow_response(context)
        elif "quality" in message_lower or "defect" in message_lower:
            return self._generate_quality_response(context)
        elif "team" in message_lower or "stability" in message_lower:
            return self._generate_team_response(context)
        elif "scorecard" in message_lower or "health" in message_lower:
            return self._generate_scorecard_response(context)
        elif "improve" in message_lower or "recommendation" in message_lower:
            return self._generate_improvement_response(context)
        else:
            return self._generate_default_response()

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
