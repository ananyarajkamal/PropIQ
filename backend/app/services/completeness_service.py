"""Deterministic Proposal Completeness Service for PropIQ.

Calculates a deterministic Proposal Completeness % metric based on validated extraction status
quality across canonical procurement topics (Price, Timeline, SLA, Payment Terms, Certifications,
Warranty, Liability, Renewal, Termination, Support).

Status Quality Mapping:
- FOUND = 1.0 (Fully addressed)
- UNCLEAR = 0.5 (Partially addressed)
- CONFLICTING = 0.0 (Unresolved contradiction)
- NOT_FOUND = 0.0 (Missing)

Note: Proposal Completeness measures proposal clarity/thoroughness and is kept strictly separate
from vendor alignment/quality scores.
"""

from typing import Dict, List, Any
from app.models import VendorFactSheet


CANONICAL_SCHEMA_TOPICS: List[str] = [
    "Price / Budget",
    "Deployment Timeline",
    "SLA / Uptime",
    "Payment Terms",
    "Certifications",
    "Warranty",
    "Liability",
    "Renewal",
    "Termination",
    "Support",
]


class CompletenessService:
    """Service calculating deterministic proposal completeness metrics."""

    def calculate_vendor_completeness(self, fact_sheet: VendorFactSheet) -> Dict[str, Any]:
        """Calculate proposal completeness metric for a single vendor fact sheet.

        Args:
            fact_sheet: VendorFactSheet instance.

        Returns:
            Dict containing completeness_percentage, status_breakdown, and topic_scores.
        """
        category_map = {c.category: c.status for c in fact_sheet.categories}

        topic_scores: Dict[str, float] = {}
        status_breakdown = {"FOUND": 0, "UNCLEAR": 0, "CONFLICTING": 0, "NOT_FOUND": 0}

        for topic in CANONICAL_SCHEMA_TOPICS:
            # Map canonical topic to vendor category status
            matching_status = "NOT_FOUND"
            for cat_name, status in category_map.items():
                if self._topic_matches_category(topic, cat_name):
                    matching_status = status.upper()
                    break

            if matching_status == "FOUND":
                score = 1.0
                status_breakdown["FOUND"] += 1
            elif matching_status == "UNCLEAR":
                score = 0.5
                status_breakdown["UNCLEAR"] += 1
            elif matching_status == "CONFLICTING":
                score = 0.0
                status_breakdown["CONFLICTING"] += 1
            else:
                score = 0.0
                status_breakdown["NOT_FOUND"] += 1

            topic_scores[topic] = score

        total_possible = len(CANONICAL_SCHEMA_TOPICS) * 1.0
        achieved_score = sum(topic_scores.values())
        completeness_pct = round((achieved_score / total_possible) * 100.0, 1)

        return {
            "vendor_name": fact_sheet.vendor_name,
            "completeness_percentage": completeness_pct,
            "achieved_score": achieved_score,
            "total_topics": len(CANONICAL_SCHEMA_TOPICS),
            "status_breakdown": status_breakdown,
            "topic_scores": topic_scores,
        }

    def calculate_session_completeness(
        self, fact_sheets: List[VendorFactSheet]
    ) -> List[Dict[str, Any]]:
        """Calculate proposal completeness metrics across all vendor fact sheets in a session."""
        return [self.calculate_vendor_completeness(fs) for fs in fact_sheets]

    def _topic_matches_category(self, canonical_topic: str, category_name: str) -> bool:
        """Check if canonical topic matches category name."""
        c1 = canonical_topic.lower()
        c2 = category_name.lower()
        if c1 in c2 or c2 in c1:
            return True
        if "price" in c1 and ("budget" in c2 or "price" in c2 or "cost" in c2):
            return True
        if "timeline" in c1 and ("deploy" in c2 or "schedule" in c2 or "timeline" in c2):
            return True
        if "sla" in c1 and ("uptime" in c2 or "sla" in c2):
            return True
        return False
