"""
Ebbinghaus Forgetting Curve Model
R(t) = e^(-λt)

λ is personalized per user+topic based on:
  - Initial understanding score
  - Adaptive updates from actual recall performance
"""

import math
import json
from datetime import datetime, timedelta
from typing import Optional


def initial_lambda(understanding_score: int) -> float:
    """
    Estimate initial forgetting rate from self-reported understanding.
    Score: 1 (barely understood) → 5 (mastered)

    λ ranges from ~0.20 (mastered) to ~1.00 (barely understood)
    """
    # Clamp score to valid range
    score = max(1, min(5, understanding_score))
    return round(1.0 / score, 4)


def retention(t: float, lam: float, stability: float = 1.0) -> float:
    """
    Calculate memory retention at time t (in days).

    R(t) = e^(-λt / S)
    where S = stability factor (increases with each successful revision)

    Returns retention as 0.0 → 1.0
    """
    return round(math.exp(-lam * t / stability), 4)


def retention_schedule(lam: float, stability: float = 1.0) -> dict:
    """
    Returns predicted retention at standard checkpoints.
    """
    checkpoints = [1, 3, 7, 14, 21, 30]
    return {
        f"day_{d}": {
            "days": d,
            "retention_pct": round(retention(d, lam, stability) * 100, 1),
            "label": _retention_label(retention(d, lam, stability))
        }
        for d in checkpoints
    }


def next_revision_time(lam: float, stability: float = 1.0, threshold: float = 0.6) -> float:
    """
    Calculate days until retention drops below threshold.
    Solve: threshold = e^(-λt/S) → t = -ln(threshold) * S / λ
    """
    if lam <= 0:
        return float("inf")
    t = (-math.log(threshold) * stability) / lam
    return round(t, 2)


def update_lambda(old_lam: float, predicted_retention: float, actual_retention: float) -> float:
    """
    Bayesian-style adaptive update of forgetting rate.

    If you remembered MORE than predicted → λ decreases (you're better)
    If you remembered LESS than predicted → λ increases (you're worse)

    λ_new = λ_old × (predicted / actual)

    Clamped to reasonable bounds [0.05, 2.0]
    """
    if actual_retention <= 0:
        actual_retention = 0.01  # avoid division by zero

    new_lam = old_lam * (predicted_retention / actual_retention)
    return round(max(0.05, min(2.0, new_lam)), 4)


def update_stability(current_stability: float, actual_retention: float) -> float:
    """
    Stability increases with successful recall (spaced repetition logic).
    Higher retention at review → bigger stability boost.
    """
    if actual_retention >= 0.8:
        factor = 2.5   # excellent recall → major boost
    elif actual_retention >= 0.6:
        factor = 1.8   # good recall
    elif actual_retention >= 0.4:
        factor = 1.2   # fair recall
    else:
        factor = 0.8   # poor recall → slight reduction

    return round(current_stability * factor, 4)


def forgetting_risk(lam: float, days_since_study: float, stability: float = 1.0) -> str:
    """
    Return risk level based on current retention.
    """
    r = retention(days_since_study, lam, stability)
    if r >= 0.75:
        return "safe"
    elif r >= 0.55:
        return "review_soon"
    elif r >= 0.35:
        return "urgent"
    else:
        return "critical"


def _retention_label(r: float) -> str:
    if r >= 0.80:
        return "Strong"
    elif r >= 0.60:
        return "Good"
    elif r >= 0.40:
        return "Fading"
    elif r >= 0.20:
        return "Weak"
    else:
        return "Forgotten"


def curve_points(lam: float, stability: float = 1.0, days: int = 30) -> list:
    """
    Generate (t, R) points for plotting the curve.
    """
    return [
        {"day": t, "retention": round(retention(t, lam, stability) * 100, 1)}
        for t in range(0, days + 1)
    ]
