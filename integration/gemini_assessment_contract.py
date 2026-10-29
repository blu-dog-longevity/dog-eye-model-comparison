"""Validate Gemini evidence-synthesis output before storing a research assessment.

This validates structure and provenance, NOT truth or veterinary accuracy.
"""
from __future__ import annotations

ALLOWED_CHANGE = {"increased", "decreased", "no_clear_change", "unable_to_compare"}
ALLOWED_OBS = {"none", "mild", "moderate", "severe", "unclear"}
OBSERVATIONS = (
    "cloudiness", "redness", "discharge", "swelling", "iris_appearance",
    "pupil_appearance", "third_eyelid", "eyelids", "eye_surface",
)

def validate_gemini_result(result: dict, *, photo_id: str, input_run_ids: list[str]) -> dict:
    if not isinstance(result, dict):
        raise ValueError("Gemini result must be a structured object")
    if result.get("photo_id") != photo_id:
        raise ValueError("Assessment photo reference mismatch")
    if not input_run_ids or len(input_run_ids) != len(set(input_run_ids)):
        raise ValueError("Input model runs must be explicitly identified")
    refs = result.get("input_run_ids")
    if not isinstance(refs,list) or set(refs) != set(input_run_ids) or len(refs) != len(set(refs)):
        raise ValueError("Gemini must reference exactly the supplied model runs")
    fields = result.get("observations")
    if not isinstance(fields,dict) or set(fields) != set(OBSERVATIONS):
        raise ValueError("Expected complete structured visual-observation fields")
    for key,value in fields.items():
        if not isinstance(value,dict) or value.get("severity") not in ALLOWED_OBS:
            raise ValueError("Invalid visual observation")
        if not isinstance(value.get("description"),str):
            raise ValueError("Observation must have a plain-language description")
    compare = result.get("comparison")
    if not isinstance(compare,dict) or compare.get("change") not in ALLOWED_CHANGE:
        raise ValueError("Comparison requires an explicit change status")
    if compare["change"] != "unable_to_compare" and not compare.get("previous_photo_id"):
        raise ValueError("Cannot report a historical change without previous photo")
    if not isinstance(result.get("model_agreement"),dict):
        raise ValueError("Model agreement and disagreements must be structured")
    if not isinstance(result.get("limitations"),list):
        raise ValueError("Uncertainty limitations must be explicit")
    if not isinstance(result.get("owner_summary"),str):
        raise ValueError("Owner summary must be text")
    if result.get("clinical_accuracy_verified") is True:
        raise ValueError("Gemini cannot independently certify clinical accuracy")
    return result

def gemini_db_payload(result: dict, *, run_id: str, dog_id: str, photo_id: str,
                      input_run_ids: list[str], prompt_version: str) -> dict:
    validated = validate_gemini_result(result, photo_id=photo_id, input_run_ids=input_run_ids)
    previous = validated["comparison"].get("previous_photo_id")
    return {
        "model_run_id":run_id,"dog_id":dog_id,"current_photo_id":photo_id,
        "previous_photo_id":previous,"input_run_ids":input_run_ids,
        "prompt_version":prompt_version,
        "observations":validated["observations"],
        "agreement":validated["model_agreement"],
        "sam_review":validated.get("sam_review",{}),
        "pro_context":validated.get("pro_context",{}),
        "image_comparability":validated["comparison"]["change"],
        "uncertainty":{"limitations":validated["limitations"]},
        "owner_summary":validated["owner_summary"],
        "research_summary":validated.get("research_summary"),
    }
