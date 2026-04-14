"""Simulate simple newsletter performance metrics by persona segment."""

from __future__ import annotations

import hashlib

from config import PERFORMANCE_HISTORY_FILE
from services.campaign_logger import CampaignLogger


class MetricsSimulator:
    """Generate deterministic but realistic performance ranges."""

    BASELINES = {
        "Creative Agency Owner": {"open_rate": 0.44, "click_rate": 0.16, "unsubscribe_rate": 0.02},
        "Operations Manager at a Small Agency": {
            "open_rate": 0.49,
            "click_rate": 0.19,
            "unsubscribe_rate": 0.015,
        },
        "Freelance Creative Professional": {
            "open_rate": 0.41,
            "click_rate": 0.14,
            "unsubscribe_rate": 0.018,
        },
    }

    def __init__(self) -> None:
        self.logger = CampaignLogger()

    def simulate(self, topic: str, campaign_entries: list) -> list:
        """Simulate metrics for each persona and persist them."""
        metrics = []
        for entry in campaign_entries:
            persona = entry["persona"]
            baseline = self.BASELINES.get(persona, self.BASELINES["Freelance Creative Professional"])
            # Deterministic scoring keeps this take-home easy to rerun and discuss in an interview setting.
            modifier = self._deterministic_modifier(topic, persona)
            total_contacts = entry.get("total_contacts", 0)
            result = {
                "campaign_id": entry["campaign_id"],
                "blog_title": entry["blog_title"],
                "persona": persona,
                "newsletter_version_id": entry["newsletter_version_id"],
                "open_rate": round(min(max(baseline["open_rate"] + modifier, 0.10), 0.75), 3),
                "click_rate": round(min(max(baseline["click_rate"] + modifier / 2, 0.03), 0.40), 3),
                "unsubscribe_rate": round(
                    min(max(baseline["unsubscribe_rate"] - modifier / 4, 0.005), 0.05), 3
                ),
                "total_contacts": total_contacts,
            }
            self.logger.append_record(PERFORMANCE_HISTORY_FILE, result)
            metrics.append(result)
        return metrics

    def _deterministic_modifier(self, topic: str, persona: str) -> float:
        """Use a stable hash so repeated runs on the same input stay easy to explain."""
        digest = hashlib.sha256(f"{topic.lower()}::{persona}".encode("utf-8")).hexdigest()
        scaled = int(digest[:4], 16) / 65535
        return round((scaled - 0.5) * 0.08, 3)
