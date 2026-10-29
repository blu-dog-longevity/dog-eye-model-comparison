import unittest
from supabase_payloads import model_run_payload, classifier_payload
from test_eye_output_validation import row

class TestSupabasePayload(unittest.TestCase):
    def test_classifier_payload_preserves_scores(self):
        source=row()
        out=classifier_payload(row=source,run_id="run",dog_id="dog")
        self.assertEqual(out["class_scores"],source["scores"])
        self.assertEqual(out["detection_boxes"][0]["xyxy"],source["box"])
        self.assertEqual(out["dog_id"],"dog")
    def test_detector_miss_has_no_classification(self):
        self.assertIsNone(classifier_payload(row={"model":"rady4","status":"no_eye_detected"},run_id="r",dog_id="d"))
    def test_run_skip(self):
        out=model_run_payload(photo_id="p",dog_id="d",model="rady4",version="v1",source_result={"status":"no_eye_detected"})
        self.assertEqual(out["status"],"skipped")
        self.assertEqual(out["error_code"],"no_eye_detected")
    def test_unknown_model_rejected(self):
        with self.assertRaises(ValueError):
            model_run_payload(photo_id="p",dog_id="d",model="other",version="v1",source_result={"status":"ok"})

if __name__=="__main__":
    unittest.main()
