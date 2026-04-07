"""
Revision Scheduler

Implements spaced repetition logic:
- Schedule next revision when R(t) < 0.6
- Sort topics by urgency (lowest retention first)
- Generate daily alert list
"""

from datetime import datetime, timedelta
from forgetting_curve import retention, next_revision_time, forgetting_risk
from typing import List


def days_since(date_str: str) -> float:
    """Calculate days elapsed since a datetime string."""
    dt = datetime.fromisoformat(date_str)
    delta = datetime.now() - dt
    return delta.total_seconds() / 86400


def get_current_retention(topic: dict) -> float:
    """Get current real-time retention % for a topic."""
    anchor = topic.get("last_revised") or topic.get("study_date")
    if not anchor:
        return 0.0
    elapsed = days_since(anchor)
    r = retention(elapsed, topic["lambda"], topic.get("stability", 1.0))
    return round(r * 100, 1)


def get_next_review_date(topic: dict) -> str:
    """Calculate the recommended next review date."""
    anchor = topic.get("last_revised") or topic.get("study_date")
    if not anchor:
        return "ASAP"

    elapsed = days_since(anchor)
    t_review = next_revision_time(topic["lambda"], topic.get("stability", 1.0), threshold=0.60)
    days_until = max(0, t_review - elapsed)

    review_date = datetime.now() + timedelta(days=days_until)
    if days_until < 1:
        return "Today"
    elif days_until < 2:
        return "Tomorrow"
    else:
        return review_date.strftime("%b %d")


def get_alerts(topics: list) -> list:
    """
    Generate revision alerts sorted by urgency.
    Returns only topics that need review (retention < 60%).
    """
    alerts = []
    for topic in topics:
        current_r = get_current_retention(topic)
        risk = forgetting_risk(
            topic["lambda"],
            days_since(topic.get("last_revised") or topic.get("study_date")),
            topic.get("stability", 1.0),
        )

        if risk in ("urgent", "critical", "review_soon"):
            alerts.append({
                "topic": topic["name"],
                "retention_pct": current_r,
                "risk": risk,
                "next_review": get_next_review_date(topic),
                "message": _alert_message(topic["name"], current_r, risk),
            })

    # Sort: critical first, then by retention ascending
    risk_order = {"critical": 0, "urgent": 1, "review_soon": 2, "safe": 3}
    alerts.sort(key=lambda x: (risk_order[x["risk"]], x["retention_pct"]))
    return alerts


def dashboard_topics(topics: list) -> list:
    """
    Enrich all topics with live retention and review info for dashboard.
    """
    enriched = []
    for topic in topics:
        current_r = get_current_retention(topic)
        elapsed = days_since(topic.get("last_revised") or topic.get("study_date"))
        enriched.append({
            **topic,
            "current_retention_pct": current_r,
            "days_elapsed": round(elapsed, 1),
            "risk": forgetting_risk(topic["lambda"], elapsed, topic.get("stability", 1.0)),
            "next_review": get_next_review_date(topic),
        })

    enriched.sort(key=lambda x: x["current_retention_pct"])
    return enriched


def _alert_message(name: str, retention_pct: float, risk: str) -> str:
    if risk == "critical":
        return f"⚠️ Revise '{name}' NOW — retention at {retention_pct:.0f}%"
    elif risk == "urgent":
        return f"🔴 '{name}' is fading fast — {retention_pct:.0f}% remaining"
    else:
        return f"🟡 Schedule review for '{name}' — {retention_pct:.0f}% retained"
