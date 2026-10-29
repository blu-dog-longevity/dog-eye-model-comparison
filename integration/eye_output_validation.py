"""Pure-data validation for archived and future MEtech eye classification outputs.

No model weights, patient images, network calls, or Supabase credentials required.
This module is NOT a veterinary diagnostic validator.
"""
from __future__ import annotations

import math
from typing import Any

RADY4 = ("Cataract", "Cherry_eye", "Iris_atrophy", "Healthy")
RADY6 = ("Cataract", "Cherry_eye", "Conjunctivitis", "Glaucoma", "Healthy", "Iris_atrophy")
MODELS = {"rady4": RADY4, "rady6": RADY6}

class InvalidModelResult(ValueError):
    pass


def validate_classification(row: dict[str, Any]) -> dict[str, Any]:
    """Validate the shape and score consistency without asserting clinical correctness."""
    model = row.get("model")
    if model not in MODELS:
        raise InvalidModelResult("Unsupported model for this validator")
    if row.get("status") == "no_eye_detected":
        if "prediction" in row or "scores" in row:
            raise InvalidModelResult("Detector failure must not include a classification")
        return {"model": model, "status": "needs_review", "reason": "no_eye_detected"}
    if row.get("status") != "ok":
        raise InvalidModelResult("Unexpected processing status")
    scores = row.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(MODELS[model]):
        raise InvalidModelResult("Scores must contain the exact model-specific classes")
    values = list(scores.values())
    if any(type(v) not in (float, int) or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise InvalidModelResult("Scores must be finite numbers within 0..1")
    if abs(sum(values) - 1.0) > 0.005:
        raise InvalidModelResult("Class scores must sum approximately to one")
    label = row.get("prediction")
    if label not in scores or scores[label] != max(values):
        raise InvalidModelResult("Prediction must match a highest-scoring class")
    raw_score = row.get("score")
    if type(raw_score) not in (float, int) or abs(raw_score - scores[label]) > 1e-5:
        raise InvalidModelResult("Top score must match predicted class score")
    box = row.get("box")
    if not isinstance(box, list) or len(box) != 4 or any(type(x) not in (float,int) or not math.isfinite(x) for x in box):
        raise InvalidModelResult("Eye detection box is required")
    if not (box[0] < box[2] and box[1] < box[3]):
        raise InvalidModelResult("Detection box must have positive area")
    confidence = row.get("detection_score")
    if type(confidence) not in (float,int) or not 0 <= confidence <= 1:
        raise InvalidModelResult("Invalid eye detector score")
    return {"model": model, "status": "candidate", "prediction": label, "scores": scores,
            "detection_box": box, "detection_score": confidence}


def owner_display_candidate(row: dict[str, Any], *, eye_crop_accepted: bool) -> dict[str, str]:
    """Only Rady-4 may be considered for display; clinical release gating is separate."""
    if row.get("model") != "rady4" or not eye_crop_accepted:
        return {"display_state": "needs_review", "displayed_label": "Unclear / Needs Review"}
    validated = validate_classification(row)
    if validated["status"] != "candidate":
        return {"display_state": "needs_review", "displayed_label": "Unclear / Needs Review"}
    return {"display_state": "candidate_only", "displayed_label": validated["prediction"]}


def validate_sam_measurement(measurement: dict[str, Any]) -> None:
    """Missing is NULL, never an invented zero; measurement quality must be explicit."""
    quality = measurement.get("quality_status")
    if quality not in {"valid", "limited", "invalid", "unavailable"}:
        raise InvalidModelResult("SAM measurement quality is required")
    value = measurement.get("measurement_value")
    if quality in {"invalid", "unavailable"} and value is not None:
        raise InvalidModelResult("Invalid/unavailable SAM measurements must be null")
    if value is not None and (type(value) not in (float,int) or not math.isfinite(value)):
        raise InvalidModelResult("SAM measurement must be finite or null")
