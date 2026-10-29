"""Offline contract tests; run: python -m unittest discover -s integration -p 'test_*.py'"""
import unittest
from eye_output_validation import (
    InvalidModelResult, validate_classification, validate_sam_measurement, owner_display_candidate,
    RADY4, RADY6,
)

def row(model="rady4"):
    classes = RADY4 if model == "rady4" else RADY6
    scores = {name: 0.1 / (len(classes) - 1) for name in classes}
    scores[classes[0]] = 0.9
    return dict(model=model, status="ok", scores=scores, prediction=classes[0],
                score=0.9, box=[10.0, 20.0, 40.0, 50.0], detection_score=0.8)

class TestEyeOutputContract(unittest.TestCase):
    def test_rady_classes(self):
        self.assertEqual(len(RADY4), 4)
        self.assertEqual(len(RADY6), 6)
        self.assertEqual(set(RADY6)-set(RADY4), {"Conjunctivitis", "Glaucoma"})
    def test_valid_rady_models(self):
        for model in ("rady4", "rady6"):
            self.assertEqual(validate_classification(row(model))["status"], "candidate")
    def test_wrong_class_order_or_model_set(self):
        r = row()
        r["scores"]["Glaucoma"] = 0
        with self.assertRaises(InvalidModelResult):
            validate_classification(r)
    def test_predicted_label_must_be_highest(self):
        r = row()
        r["prediction"] = "Healthy"
        with self.assertRaises(InvalidModelResult):
            validate_classification(r)
    def test_invalid_crop(self):
        r = row()
        r["box"] = [10,20,10,50]
        with self.assertRaises(InvalidModelResult):
            validate_classification(r)
    def test_no_detection_is_review(self):
        r = {"model":"rady4","status":"no_eye_detected"}
        self.assertEqual(validate_classification(r)["status"], "needs_review")
        self.assertEqual(owner_display_candidate(r, eye_crop_accepted=True)["display_state"],"needs_review")
    def test_only_rady4_is_customer_candidate(self):
        self.assertEqual(owner_display_candidate(row("rady6"), eye_crop_accepted=True)["display_state"],"needs_review")
        self.assertEqual(owner_display_candidate(row(), eye_crop_accepted=False)["display_state"],"needs_review")
        self.assertEqual(owner_display_candidate(row(), eye_crop_accepted=True)["display_state"],"candidate_only")
    def test_sam_missing_null(self):
        validate_sam_measurement({"quality_status":"unavailable","measurement_value":None})
        with self.assertRaises(InvalidModelResult):
            validate_sam_measurement({"quality_status":"invalid","measurement_value":0})
    def test_sam_finite(self):
        with self.assertRaises(InvalidModelResult):
            validate_sam_measurement({"quality_status":"valid","measurement_value":float("nan")})

if __name__ == "__main__":
    unittest.main()
