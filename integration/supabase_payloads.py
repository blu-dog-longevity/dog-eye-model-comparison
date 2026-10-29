"""Translate archived Rady inference records into Supabase write payloads.

Pure functions, no credentials, images, or database connections. The caller must
authenticate, enforce dog ownership, and create its own photo/run records.
"""
from __future__ import annotations
from typing import Any
try:
    from .eye_output_validation import validate_classification
except ImportError:
    from eye_output_validation import validate_classification

def classifier_payload(*, row: dict[str, Any], run_id: str, dog_id: str) -> dict[str, Any] | None:
    result = validate_classification(row)
    if result["status"] == "needs_review":
        return None
    return {
        "model_run_id": run_id,
        "dog_id": dog_id,
        "predicted_label": result["prediction"],
        "class_scores": result["scores"],
        "detection_boxes": [{
            "xyxy": result["detection_box"],
            "score": result["detection_score"],
        }],
        "assessment_status": "unreviewed",
    }

def model_run_payload(*, photo_id: str, dog_id: str, model: str, version: str,
                      source_result: dict[str, Any]) -> dict[str, Any]:
    if model not in ("rady4","rady6","dog_disease_predictor","sam2_1","gemini"):
        raise ValueError("Unrecognized model")
    status = source_result.get("status")
    state = {"ok":"completed", "no_eye_detected":"skipped", "failed":"failed"}.get(status)
    if state is None:
        raise ValueError("Unsupported source status")
    return {
        "photo_id": photo_id, "dog_id": dog_id, "model_name": model,
        "model_version": version, "status": state,
        "error_code": "no_eye_detected" if status == "no_eye_detected" else None,
        "output_metadata": {"source_status": status},
    }
