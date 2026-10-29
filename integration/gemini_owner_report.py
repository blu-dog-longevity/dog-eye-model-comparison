"""Owner-facing Gemini report contract; no research-model outputs required.

Gemini supplies visual observations, not veterinary diagnoses. This module does
not call Gemini or Supabase; validate backend output before display persistence.
"""
from __future__ import annotations
from .gemini_assessment_contract import OBSERVATIONS, ALLOWED_OBS, ALLOWED_CHANGE

def owner_report_payload(result: dict, *, dog_id: str, photo_id: str,
                         gemini_assessment_id: str, prompt_version: str) -> dict:
    if result.get("photo_id") != photo_id:
        raise ValueError("Photo mismatch")
    observations = result.get("observations")
    if not isinstance(observations,dict) or set(observations) != set(OBSERVATIONS):
        raise ValueError("Missing required visible observations")
    for obs in observations.values():
        if not isinstance(obs,dict) or obs.get("severity") not in ALLOWED_OBS or not isinstance(obs.get("description"),str):
            raise ValueError("Invalid observation")
    if result.get("diagnosis") or result.get("clinical_accuracy_verified") is True:
        raise ValueError("Owner report must not contain a model diagnosis or asserted clinical accuracy")
    status=result.get("display_state")
    if status not in ("ready","needs_review","unavailable"):
        raise ValueError("Invalid display status")
    summary=result.get("owner_summary")
    if not isinstance(summary,str) or not summary.strip():
        raise ValueError("Owner report must have plain language findings")
    comparison=result.get("comparison",{})
    if not isinstance(comparison,dict) or comparison.get("change") not in ALLOWED_CHANGE:
        raise ValueError("Historical comparison status required")
    if comparison["change"] != "unable_to_compare" and not comparison.get("previous_photo_id"):
        raise ValueError("Historical change requires prior same-eye photo reference")
    return {
        "photo_id":photo_id, "dog_id":dog_id,
        "gemini_assessment_id":gemini_assessment_id,
        "classifier_run_id":None,
        "display_state":status,
        "displayed_label":None,
        "owner_explanation":summary,
        "presented_payload":{
            "source":"gemini", "prompt_version":prompt_version,
            "observations":observations, "comparison":comparison,
            "limitations":result.get("limitations",[]),
            "actions":result.get("actions",[]),
            "no_diagnosis":True,
        },
    }
