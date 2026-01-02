"""
Example: Coaching Output

This module demonstrates how a complete coaching analysis would look.
"""

from datetime import datetime, timedelta
from typing import List

from backend.models import (
    ActionableStep,
    CoachingReport,
    Evidence,
    ExecutiveSummary,
    ImprovementEffort,
    ImprovementImpact,
    ImprovementProposal,
    Insight,
    RootCauseCategory,
    Scope,
)


def generate_example_coaching_report() -> CoachingReport:
    """
    Generate an example coaching report for demonstration purposes.

    This shows what the final output of the Evaluation Coach looks like.
    """

    # Time period
    end_date = datetime(2026, 1, 2)
    start_date = end_date - timedelta(days=28)  # Last 4 weeks / 2 sprints

    # Executive Summary
    executive_summary = ExecutiveSummary(
        scope="Platform Team",
        scope_type=Scope.TEAM,
        time_period="Sprints 42-43 (Dec 2025)",
        key_achievements=[
            "Maintained consistent velocity (23 points avg) across both sprints",
            "Reduced average lead time from 96h to 72h (25% improvement)",
            "Zero critical bugs escaped to production",
        ],
        key_challenges=[
            "High WIP (avg 12 items) exceeding team capacity",
            "Code review becoming a bottleneck (avg wait time: 18h)",
            "30% scope addition mid-sprint in Sprint 43",
        ],
        overall_health_score=68.5,
        predictability_score=0.72,  # 72% commitment reliability
        flow_efficiency_score=0.42,  # 42% flow efficiency
        top_priorities=[
            "Reduce WIP by implementing WIP limits",
            "Address code review bottleneck",
            "Improve mid-sprint scope management",
        ],
        trends={
            "lead_time": "improving",
            "cycle_time": "stable",
            "throughput": "stable",
            "blocked_time": "declining",  # Positive: less blocking
            "scope_stability": "declining",  # Negative: more scope changes
        },
    )

    # Insights
    insights = [
        Insight(
            title="Code Review is the Primary Bottleneck",
            description=(
                "Analysis shows that 45% of total cycle time is spent waiting for code review. "
                "The average wait time for review is 18 hours, with some items waiting up to 48 hours. "
                "This is significantly impacting flow efficiency."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            evidence=[
                Evidence(
                    description="Average code review wait time: 18 hours",
                    metric_name="code_review_wait_time",
                    metric_value=18.0,
                    data_source="Status transition analysis",
                    confidence=0.95,
                ),
                Evidence(
                    description="45% of cycle time spent in 'In Review' status",
                    metric_name="review_time_percentage",
                    metric_value=0.45,
                    data_source="Flow efficiency calculation",
                    confidence=0.92,
                ),
            ],
            implication=(
                "The team is losing nearly half of their potential throughput to review delays. "
                "This also increases context switching costs and reduces flow predictability."
            ),
            related_proposals=["prop-1", "prop-2"],
        ),
        Insight(
            title="High WIP Indicates Overcommitment",
            description=(
                "The team's average WIP of 12 items significantly exceeds the team size of 6 developers. "
                "This results in excessive context switching and reduced focus."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            evidence=[
                Evidence(
                    description="Average WIP: 12 items",
                    metric_name="wip_average",
                    metric_value=12.0,
                    data_source="WIP calculation",
                    confidence=0.98,
                ),
                Evidence(
                    description="Team size: 6 developers",
                    metric_name="team_size",
                    metric_value=6.0,
                    data_source="Team configuration",
                    confidence=1.0,
                ),
            ],
            implication=(
                "High WIP leads to increased lead times, reduced quality, and team stress. "
                "The optimal WIP is typically equal to or slightly less than team size."
            ),
            related_proposals=["prop-3"],
        ),
        Insight(
            title="Scope Additions Correlate with Missed Commitments",
            description=(
                "Sprint 43 had 30% scope addition after sprint start, and commitment reliability dropped to 65% "
                "(vs 80% in Sprint 42 with only 10% scope change)."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            evidence=[
                Evidence(
                    description="Sprint 43 scope change rate: 30%",
                    metric_name="scope_change_rate",
                    metric_value=0.30,
                    data_source="Sprint analysis",
                    confidence=1.0,
                ),
                Evidence(
                    description="Sprint 43 commitment reliability: 65%",
                    metric_name="commitment_reliability",
                    metric_value=0.65,
                    data_source="Sprint analysis",
                    confidence=1.0,
                ),
            ],
            implication=(
                "Mid-sprint scope changes reduce predictability and team morale. "
                "This pattern suggests issues with sprint planning or stakeholder management."
            ),
            related_proposals=["prop-4"],
        ),
    ]

    # Improvement Proposals
    improvement_proposals = [
        ImprovementProposal(
            id="prop-1",
            title="Implement Dedicated Code Review Time Blocks",
            description=(
                "Establish dedicated 30-minute code review blocks twice daily (10:30 AM and 3:00 PM) "
                "where all team members pause active development to review pending PRs."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            root_cause_category=RootCauseCategory.PROCESS,
            addresses_patterns=["bottleneck-1"],
            expected_impact=ImprovementImpact.HIGH,
            implementation_effort=ImprovementEffort.LOW,
            priority_score=92.0,
            evidence=[
                Evidence(
                    description="Code review bottleneck causing 18h avg wait time",
                    metric_name="code_review_wait_time",
                    metric_value=18.0,
                    data_source="Pattern detection",
                    confidence=0.95,
                ),
            ],
            rationale=(
                "Dedicated time blocks ensure reviews happen promptly and predictably. "
                "This approach, used successfully in other high-performing teams, reduces wait time "
                "while maintaining focus during deep work periods."
            ),
            steps=[
                ActionableStep(
                    step_number=1,
                    description="Team agrees on review time blocks (10:30 AM and 3:00 PM)",
                    responsible_role="Scrum Master",
                    estimated_effort="1 hour (team discussion)",
                    dependencies=[],
                ),
                ActionableStep(
                    step_number=2,
                    description="Add review blocks to team calendar with notifications",
                    responsible_role="Scrum Master",
                    estimated_effort="15 minutes",
                    dependencies=[1],
                ),
                ActionableStep(
                    step_number=3,
                    description="Monitor and track review wait times for 2 weeks",
                    responsible_role="Scrum Master",
                    estimated_effort="30 minutes per week",
                    dependencies=[2],
                ),
                ActionableStep(
                    step_number=4,
                    description="Retrospective: Assess effectiveness and adjust",
                    responsible_role="Scrum Master",
                    estimated_effort="1 hour",
                    dependencies=[3],
                ),
            ],
            success_metrics=[
                "Code review wait time reduced to < 4 hours",
                "85% of PRs reviewed within same day",
                "Team satisfaction with review process improves",
            ],
            target_improvement="Reduce code review wait time from 18h to < 4h (78% improvement)",
            risks=[
                "Team may forget or skip review blocks initially",
                "May not solve the issue if reviewers lack expertise",
            ],
            prerequisites=[
                "Team buy-in and commitment",
                "Calendar tool accessible to all team members",
            ],
            estimated_timeline="2 weeks to implement and stabilize",
            quick_wins=[
                "Start tomorrow with just one daily review block",
                "Use Slack reminders to reinforce the habit",
            ],
        ),
        ImprovementProposal(
            id="prop-2",
            title="Rotate Code Review Responsibilities",
            description=(
                "Implement a rotating 'Review Lead' role where one team member each day has primary "
                "responsibility for ensuring all PRs get reviewed promptly."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            root_cause_category=RootCauseCategory.PROCESS,
            addresses_patterns=["bottleneck-1"],
            expected_impact=ImprovementImpact.MEDIUM,
            implementation_effort=ImprovementEffort.LOW,
            priority_score=75.0,
            evidence=[
                Evidence(
                    description="No clear ownership of review process",
                    data_source="Process observation",
                    confidence=0.80,
                ),
            ],
            rationale=(
                "Clear ownership ensures someone is always monitoring the review queue. "
                "Rotation distributes the responsibility and builds review skills across the team."
            ),
            steps=[
                ActionableStep(
                    step_number=1,
                    description="Define Review Lead responsibilities",
                    responsible_role="Tech Lead",
                    estimated_effort="1 hour",
                    dependencies=[],
                ),
                ActionableStep(
                    step_number=2,
                    description="Create rotation schedule",
                    responsible_role="Scrum Master",
                    estimated_effort="30 minutes",
                    dependencies=[1],
                ),
                ActionableStep(
                    step_number=3,
                    description="Run for 2-week trial period",
                    responsible_role="Team",
                    estimated_effort="Ongoing",
                    dependencies=[2],
                ),
            ],
            success_metrics=[
                "All PRs acknowledged within 2 hours",
                "No PRs waiting > 8 hours",
            ],
            target_improvement="Ensure every PR has a designated reviewer within 2 hours",
            risks=[
                "Single point of failure if Review Lead is unavailable",
            ],
            prerequisites=[
                "Clear communication of daily rotation",
            ],
            estimated_timeline="1 week to launch, 2 weeks to stabilize",
            quick_wins=[
                "Start tomorrow with volunteer for first Review Lead",
            ],
        ),
        ImprovementProposal(
            id="prop-3",
            title="Implement WIP Limits per Team Member",
            description=(
                "Set a WIP limit of 2 items per team member (total team WIP = 12, but aim for 6-8 active). "
                "Use visual WIP limits on the team board."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            root_cause_category=RootCauseCategory.CAPACITY,
            addresses_patterns=["pattern-high-wip"],
            expected_impact=ImprovementImpact.HIGH,
            implementation_effort=ImprovementEffort.MEDIUM,
            priority_score=85.0,
            evidence=[
                Evidence(
                    description="Current avg WIP (12) is 2x team size (6)",
                    metric_name="wip_average",
                    metric_value=12.0,
                    data_source="WIP calculation",
                    confidence=0.98,
                ),
            ],
            rationale=(
                "WIP limits force the team to finish work before starting new work, improving focus and flow. "
                "Research shows optimal WIP is close to team size, not 2x team size."
            ),
            steps=[
                ActionableStep(
                    step_number=1,
                    description="Team workshop: Explain WIP limits and benefits",
                    responsible_role="Agile Coach",
                    estimated_effort="2 hours",
                    dependencies=[],
                ),
                ActionableStep(
                    step_number=2,
                    description="Agree on WIP limit (recommend: 2 items per person)",
                    responsible_role="Team",
                    estimated_effort="1 hour",
                    dependencies=[1],
                ),
                ActionableStep(
                    step_number=3,
                    description="Configure WIP limits on Jira board",
                    responsible_role="Scrum Master",
                    estimated_effort="30 minutes",
                    dependencies=[2],
                ),
                ActionableStep(
                    step_number=4,
                    description="Daily standup: Check WIP compliance",
                    responsible_role="Team",
                    estimated_effort="Ongoing",
                    dependencies=[3],
                ),
            ],
            success_metrics=[
                "Average WIP reduced to <= 8 items",
                "Lead time reduced by >= 20%",
                "Team reports improved focus",
            ],
            target_improvement="Reduce WIP from 12 to 6-8 items (33-50% reduction)",
            risks=[
                "Team may resist perceived constraint on freedom",
                "May expose other bottlenecks previously hidden by high WIP",
            ],
            prerequisites=[
                "Team understands the 'why' behind WIP limits",
                "Leadership support for saying 'no' to new work when at WIP limit",
            ],
            estimated_timeline="4 weeks to see measurable impact",
            quick_wins=[
                "Start with soft limit and transparency (no hard enforcement yet)",
            ],
        ),
        ImprovementProposal(
            id="prop-4",
            title="Strengthen Sprint Commitment and Scope Protection",
            description=(
                "Establish a clear sprint commitment process with explicit criteria for accepting "
                "mid-sprint work. Require Product Owner approval and impact analysis for any scope changes."
            ),
            scope="Platform Team",
            scope_type=Scope.TEAM,
            root_cause_category=RootCauseCategory.SCOPE_MANAGEMENT,
            addresses_patterns=["pattern-scope-instability"],
            expected_impact=ImprovementImpact.HIGH,
            implementation_effort=ImprovementEffort.MEDIUM,
            priority_score=88.0,
            evidence=[
                Evidence(
                    description="Sprint 43: 30% scope addition → 65% commitment reliability",
                    metric_name="scope_change_correlation",
                    metric_value=0.30,
                    data_source="Sprint analysis",
                    confidence=0.95,
                ),
            ],
            rationale=(
                "Frequent mid-sprint scope changes destroy predictability and team morale. "
                "Clear criteria and process help balance responsiveness with stability."
            ),
            steps=[
                ActionableStep(
                    step_number=1,
                    description="Define criteria for accepting mid-sprint work (emergencies only)",
                    responsible_role="Product Owner + Team",
                    estimated_effort="2 hours",
                    dependencies=[],
                ),
                ActionableStep(
                    step_number=2,
                    description="Create 'scope change impact assessment' template",
                    responsible_role="Scrum Master",
                    estimated_effort="1 hour",
                    dependencies=[1],
                ),
                ActionableStep(
                    step_number=3,
                    description="Communicate new process to stakeholders",
                    responsible_role="Product Owner",
                    estimated_effort="1 week",
                    dependencies=[2],
                ),
                ActionableStep(
                    step_number=4,
                    description="Track and report scope change requests and decisions",
                    responsible_role="Scrum Master",
                    estimated_effort="Ongoing",
                    dependencies=[3],
                ),
            ],
            success_metrics=[
                "Scope change rate reduced to < 10%",
                "Commitment reliability improved to >= 80%",
                "Zero unplanned 'emergency' additions (or documented as true emergencies)",
            ],
            target_improvement="Reduce scope change rate from 30% to < 10%",
            risks=[
                "Stakeholders may perceive team as less responsive",
                "Requires Product Owner to have difficult conversations",
            ],
            prerequisites=[
                "Leadership support for scope protection",
                "Product Owner empowerment to say 'no' or 'next sprint'",
            ],
            estimated_timeline="2-3 sprints to establish new norms",
            quick_wins=[
                "Start tracking all scope change requests (even if still accepting them)",
                "Make scope changes visible in sprint review",
            ],
        ),
    ]

    # Prioritize proposals
    sorted_proposals = sorted(
        improvement_proposals, key=lambda p: p.priority_score, reverse=True
    )
    prioritized_action_ids = [p.id for p in sorted_proposals]

    # Reasoning chain (for explainability)
    reasoning_chain = [
        "1. Analyzed 47 issues completed across Sprints 42-43",
        "2. Calculated flow metrics: Throughput=1.68 items/day, WIP=12, Lead Time P50=72h",
        "3. Detected bottleneck: 'In Review' status accounts for 45% of cycle time",
        "4. Detected pattern: High WIP (12 items) vs team size (6 people) = 2x ratio",
        "5. Analyzed sprint predictability: Sprint 42 (80% reliability, 10% scope change) vs Sprint 43 (65% reliability, 30% scope change)",
        "6. Correlation found: Scope changes negatively impact commitment reliability (r=-0.85)",
        "7. Retrieved knowledge: Kanban WIP limit principles, SAFe sprint commitment practices",
        "8. Generated 4 improvement proposals addressing root causes",
        "9. Prioritized by impact/effort ratio and urgency",
        "10. Validated recommendations against Agile/SAFe best practices",
    ]

    # Create final report
    report = CoachingReport(
        report_id=f"COACH-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        generated_at=datetime.utcnow(),
        scope="Platform Team",
        scope_type=Scope.TEAM,
        analysis_period_start=start_date,
        analysis_period_end=end_date,
        executive_summary=executive_summary,
        insights=insights,
        improvement_proposals=improvement_proposals,
        prioritized_actions=prioritized_action_ids,
        knowledge_sources_used=[
            "SAFe 5.1 Team and Technical Agility",
            "Kanban: Successful Evolutionary Change for Your Technology Business",
            "Actionable Agile Metrics for Predictability",
            "The Phoenix Project (Theory of Constraints)",
        ],
        reasoning_chain=reasoning_chain,
        confidence_level="High",
        data_completeness=0.92,
    )

    return report


def print_coaching_report(report: CoachingReport):
    """Pretty-print a coaching report to console."""

    print("\n" + "=" * 80)
    print(f"EVALUATION COACH REPORT")
    print(f"Report ID: {report.report_id}")
    print(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    print(f"\n📊 SCOPE: {report.scope} ({report.scope_type.value})")
    print(
        f"📅 PERIOD: {report.analysis_period_start.date()} to {report.analysis_period_end.date()}"
    )

    summary = report.executive_summary
    print(f"\n{'─' * 80}")
    print("EXECUTIVE SUMMARY")
    print(f"{'─' * 80}")
    print(f"Overall Health Score: {summary.overall_health_score}/100")
    print(f"Predictability: {summary.predictability_score:.0%}")
    print(f"Flow Efficiency: {summary.flow_efficiency_score:.0%}")

    print(f"\n✅ KEY ACHIEVEMENTS:")
    for achievement in summary.key_achievements:
        print(f"  • {achievement}")

    print(f"\n⚠️  KEY CHALLENGES:")
    for challenge in summary.key_challenges:
        print(f"  • {challenge}")

    print(f"\n🎯 TOP PRIORITIES:")
    for i, priority in enumerate(summary.top_priorities, 1):
        print(f"  {i}. {priority}")

    print(f"\n{'─' * 80}")
    print(f"INSIGHTS ({len(report.insights)})")
    print(f"{'─' * 80}")

    for i, insight in enumerate(report.insights, 1):
        print(f"\n{i}. {insight.title}")
        print(f"   {insight.description}")
        print(f"   💡 Implication: {insight.implication}")
        print(f"   📈 Evidence: {len(insight.evidence)} data points")

    print(f"\n{'─' * 80}")
    print(f"IMPROVEMENT PROPOSALS ({len(report.improvement_proposals)})")
    print(f"{'─' * 80}")

    for i, proposal_id in enumerate(report.prioritized_actions, 1):
        proposal = next(p for p in report.improvement_proposals if p.id == proposal_id)

        print(f"\n{i}. {proposal.title}")
        print(
            f"   Priority: {proposal.priority_score}/100 | Impact: {proposal.expected_impact.value} | Effort: {proposal.implementation_effort.value}"
        )
        print(f"   {proposal.description}")
        print(f"   🎯 Target: {proposal.target_improvement}")
        print(f"   ⏱️  Timeline: {proposal.estimated_timeline}")
        print(f"   📋 Steps: {len(proposal.steps)} actionable steps")
        if proposal.quick_wins:
            print(f"   ⚡ Quick Wins:")
            for qw in proposal.quick_wins:
                print(f"      • {qw}")

    print(f"\n{'─' * 80}")
    print("METHODOLOGY & EXPLAINABILITY")
    print(f"{'─' * 80}")
    print(f"Confidence Level: {report.confidence_level}")
    print(f"Data Completeness: {report.data_completeness:.0%}")
    print(f"\nKnowledge Sources:")
    for source in report.knowledge_sources_used:
        print(f"  • {source}")

    print(f"\nReasoning Chain:")
    for step in report.reasoning_chain:
        print(f"  {step}")

    print(f"\n{'─' * 80}")
    print(report.coaching_note)
    print("=" * 80 + "\n")


if __name__ == "__main__":
    """Generate and print example report."""
    report = generate_example_coaching_report()
    print_coaching_report(report)
