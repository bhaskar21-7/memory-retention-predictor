"""
Adaptive Lambda Updater

This is the core of the personalization system.
Each revision teaches the model about YOUR specific forgetting behavior.
"""

from forgetting_curve import update_lambda, update_stability, retention
from datetime import datetime
import json


def record_revision(topic: dict, actual_retention_pct: float, days_elapsed: float) -> dict:
    """
    Record a revision attempt and update the topic's personalized parameters.

    Args:
        topic: topic dict from user_data.json
        actual_retention_pct: how much user recalled (0–100)
        days_elapsed: days since last study/revision

    Returns:
        Updated topic dict with new λ, stability, and revision history
    """
    actual = actual_retention_pct / 100.0
    predicted = retention(days_elapsed, topic["lambda"], topic.get("stability", 1.0))

    old_lambda = topic["lambda"]
    new_lambda = update_lambda(old_lambda, predicted, actual)
    new_stability = update_stability(topic.get("stability", 1.0), actual)

    # Track the accuracy improvement over time
    prediction_error = abs(predicted - actual)
    accuracy_pct = round((1 - prediction_error) * 100, 1)

    revision_record = {
        "date": datetime.now().isoformat(),
        "days_elapsed": round(days_elapsed, 2),
        "predicted_retention": round(predicted * 100, 1),
        "actual_retention": round(actual * 100, 1),
        "lambda_before": old_lambda,
        "lambda_after": new_lambda,
        "accuracy_pct": accuracy_pct,
    }

    topic["lambda"] = new_lambda
    topic["stability"] = new_stability
    topic["revision_count"] = topic.get("revision_count", 0) + 1
    topic["last_revised"] = datetime.now().isoformat()

    if "revision_history" not in topic:
        topic["revision_history"] = []
    topic["revision_history"].append(revision_record)

    return topic


def model_accuracy_over_time(revision_history: list) -> list:
    """
    Returns the model's accuracy improvement across revisions.
    This is the key experiment result for your LinkedIn post!
    """
    return [
        {
            "revision": i + 1,
            "accuracy_pct": rev["accuracy_pct"],
            "lambda": rev["lambda_after"],
        }
        for i, rev in enumerate(revision_history)
    ]
