"""Create a concise AI-style summary from simulated campaign results."""

from __future__ import annotations

from datetime import datetime

from config import LATEST_SUMMARY_FILE


class PerformanceAnalyzer:
    """Generate a plain-language campaign summary and next-step recommendation."""

    def analyze(self, topic: str, content: dict, metrics: list) -> str:
        """Build and save a markdown summary for the latest run."""
        if not metrics:
            raise ValueError("Metrics are required to generate a performance summary.")

        best_persona = max(metrics, key=lambda item: (item["click_rate"], item["open_rate"]))
        best_newsletter = next(
            (item for item in content.get("newsletters", []) if item["persona"] == best_persona["persona"]),
            {},
        )
        pattern = self._infer_pattern(best_newsletter)
        recommendation = self._build_recommendation(best_persona, pattern)

        summary = (
            f"# NovaMind Campaign Summary\n\n"
            f"**Run date:** {datetime.utcnow().isoformat()}Z\n"
            f"**Topic:** {topic}\n"
            f"**Blog title:** {content.get('blog_title')}\n\n"
            f"_Assumption: performance figures below are simulated locally to demonstrate campaign analysis logic._\n\n"
            f"## Performance Overview\n\n"
            f"The strongest-performing segment was **{best_persona['persona']}** with an "
            f"open rate of **{best_persona['open_rate']:.1%}**, a click rate of "
            f"**{best_persona['click_rate']:.1%}**, and an unsubscribe rate of "
            f"**{best_persona['unsubscribe_rate']:.1%}**.\n\n"
            f"A likely driver of this result was {pattern}. The winning newsletter used the subject line "
            f"\"{best_newsletter.get('subject_line', 'N/A')}\" and emphasized a clear, practical value proposition.\n\n"
            f"## Recommendation\n\n"
            f"{recommendation}\n"
        )

        with LATEST_SUMMARY_FILE.open("w", encoding="utf-8") as file:
            file.write(summary)

        return summary

    def _infer_pattern(self, newsletter: dict) -> str:
        """Infer a simple content pattern from the best-performing newsletter copy."""
        body = newsletter.get("body", "").lower()
        if "strategy" in body or "client" in body:
            return "messaging that tied automation directly to strategic client value"
        if "workflow" in body or "process" in body:
            return "process-focused messaging that made operational benefits feel concrete"
        return "concise messaging that connected automation to immediate time savings"

    def _build_recommendation(self, best_persona: dict, pattern: str) -> str:
        """Return a next-step recommendation based on the best result."""
        return (
            f"For the next campaign, keep targeting **{best_persona['persona']}** with a similar angle and test "
            f"a second variant that doubles down on {pattern}. A practical follow-up experiment would be comparing "
            "a benefit-led subject line against a workflow-specific subject line while keeping the rest of the email "
            "structure consistent."
        )
