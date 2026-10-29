"""Pure stdlib validation for MEtech eye model results. No inference, network or database writes."""
from __future__ import annotations
from math import isfinite
from typing import Any

RADY4 = ('Cataract', 'Cherry_eye', 'Iris_atrophy', 'Healthy')
RADY6 = ('Cataract', 'Cherry_eye', 'Conjunctivitis', 'Glaucoma', 'Healthy', 'Iris_atrophy')
MODEL_CLASSES = {'rady4': RADY4, 'rady6': RADY6}

class InvalidModelOutput(ValueError):
    pass

def normalize_classification(model: str, result: dict[str, Any]) -> dict[str, Any]:
    """Preserve full Rady class scores; refuse incomplete or invalid vectors."""
    if model not in MODEL_CLASSES:
        raise InvalidModelOutput(f'Unsupported Rady model: {model}')
    classes = MODEL_CLASSES[model]
    scores = result.get('scores')
    if not isinstance(scores, dict) or set(scores) != set(classes):
        raise InvalidModelOutput('Missing, extra, or incorrectly named class scores')
    for label in classes:
        v = scores[label]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v < 0 or v > 1:
            raise InvalidModelOutput(f'Invalid score for {label}')
    if not 0.99 <= sum(scores.values()) <= 1.01:
        raise InvalidModelOutput('Scores do not sum approximately to one')
    prediction = result.get('prediction')
    if prediction not in classes or prediction != max(classes, key=lambda k: scores[k]):
        raise InvalidModelOutput('Prediction disagrees with score vector')
    return {'model_name': model, 'predicted_label': prediction, 'class_scores': {key: float(scores[key]) for key in classes}, 'raw_score': float(scores[prediction]), 'is_clinically_validated': False}

def proposed_owner_display(model: str, classification: dict[str, Any] | None, *, eye_detected: bool, crop_verified: bool, quality_approved: bool, release_approved: bool = False) -> dict[str, Any]:
    """Fail closed. Draft never publishes a label without explicit release approval."""
    if not (model == 'rady4' and eye_detected and crop_verified and quality_approved and release_approved and classification):
        return {'display_state': 'needs_review', 'displayed_label': None, 'owner_explanation': 'Photo needs review. Image analysis alone is not a veterinary diagnosis.'}
    if classification.get('model_name') != 'rady4' or classification.get('predicted_label') not in RADY4:
        return {'display_state': 'needs_review', 'displayed_label': None, 'owner_explanation': 'Photo needs review.'}
    return {'display_state': 'ready', 'displayed_label': classification['predicted_label'], 'owner_explanation': 'Preliminary image finding; not a veterinary diagnosis.'}

def normalize_sam_measurement(name: str, value: float | None, *, quality: str, unit: str | None = None) -> dict[str, Any]:
    if quality not in {'unassessed', 'valid', 'limited', 'invalid', 'unavailable'}:
        raise InvalidModelOutput('Invalid SAM quality')
    if value is not None and (isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value)):
        raise InvalidModelOutput('SAM value must be finite or null')
    if quality in {'invalid', 'unavailable'} and value is not None:
        raise InvalidModelOutput('Invalid or unavailable SAM measurements must be null')
    if quality == 'valid' and value is None:
        raise InvalidModelOutput('Valid SAM measurements require a value')
    return {'measurement_name': name, 'measurement_value': float(value) if value is not None else None, 'measurement_unit': unit, 'quality_status': quality}
