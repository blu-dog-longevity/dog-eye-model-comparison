import unittest
from gemini_owner_report import owner_report_payload
from gemini_assessment_contract import OBSERVATIONS

def sample():
    return {"photo_id":"p","observations":{k:{"severity":"unclear","description":"Not assessable"} for k in OBSERVATIONS},
            "display_state":"needs_review","owner_summary":"Photo requires review.",
            "comparison":{"change":"unable_to_compare","previous_photo_id":None},"limitations":["Lighting"]}

class GeminiOwnerTests(unittest.TestCase):
    def payload(self,report):
        return owner_report_payload(report,dog_id="d",photo_id="p",gemini_assessment_id="g",prompt_version="owner-v1")
    def test_no_research_runs_required(self):
        out=self.payload(sample())
        self.assertIsNone(out["classifier_run_id"])
        self.assertIsNone(out["displayed_label"])
        self.assertEqual(out["presented_payload"]["source"],"gemini")
    def test_reject_diagnosis(self):
        x=sample();x["diagnosis"]="Cataract"
        with self.assertRaises(ValueError): self.payload(x)
    def test_reject_unanchored_change(self):
        x=sample();x["comparison"]["change"]="increased"
        with self.assertRaises(ValueError): self.payload(x)
    def test_reject_photo_mismatch(self):
        x=sample();x["photo_id"]="another"
        with self.assertRaises(ValueError): self.payload(x)

if __name__=="__main__":
    unittest.main()
