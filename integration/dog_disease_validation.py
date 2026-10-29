"""Strict research-only validator for the archived twenty-class dog disease model."""
from __future__ import annotations
import math

DOG_DISEASE_CLASSES = (
    "Acral Lick Dermatitis", "Acute moist dermatitis", "Canine atopic dermatitis",
    "Cherry Eye", "Ear infections", "External Parasites", "Folliculitis", "Healthy",
    "Leishmaniasis", "Lupus", "Nuclear sclerosis", "Otitis externa", "Pruritus",
    "Pyoderma", "Rabies", "Ringworm", "Sarcoptic Mange", "Sebaceous adenitis",
    "Seborrhea", "Skin tumor",
)

def dog_disease_payload(source: dict, *, run_id: str, dog_id: str) -> dict:
    if source.get("model") != "dog_disease_predictor" or source.get("status") != "ok":
        raise ValueError("Expected a completed DogDiseasePredictor result")
    scores = source.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(DOG_DISEASE_CLASSES):
        raise ValueError("Expected exactly 20 trained classes")
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1
           for v in scores.values()):
        raise ValueError("Scores must be finite values between zero and one")
    if abs(sum(scores.values()) - 1) > .005:
        raise ValueError("Class scores do not sum to one")
    prediction = source.get("prediction")
    if prediction not in scores or scores[prediction] != max(scores.values()):
        raise ValueError("Prediction does not match class scores")
    if abs(source.get("score", -1) - scores[prediction]) > .00001:
        raise ValueError("Top score does not match")
    return {
        "model_run_id": run_id, "dog_id": dog_id,
        "predicted_label": prediction, "class_scores": scores,
        "detection_boxes": [], "assessment_status": "unreviewed",
    }
