import unittest
from gemini_assessment_contract import OBSERVATIONS,validate_gemini_result,gemini_db_payload

def sample():
    return {
        "photo_id":"photo-one","input_run_ids":["run-rady4","run-rady6","run-sam"],
        "observations":{k:{"severity":"unclear","description":"No reliable view"} for k in OBSERVATIONS},
        "comparison":{"change":"unable_to_compare","previous_photo_id":None},
        "model_agreement":{"agreement":[],"disagreements":[]},
        "limitations":["Image resolution may be inadequate"],
        "clinical_accuracy_verified":False,"owner_summary":"Results require review."
    }

class GeminiContractTests(unittest.TestCase):
    def test_valid_structured_payload(self):
        x=sample()
        out=gemini_db_payload(x,run_id="run-gemini",dog_id="dog",photo_id="photo-one",
                              input_run_ids=x["input_run_ids"],prompt_version="research-v1")
        self.assertEqual(out["previous_photo_id"],None)
        self.assertEqual(out["prompt_version"],"research-v1")
    def test_no_unreferenced_model_results(self):
        x=sample()
        with self.assertRaises(ValueError):
            validate_gemini_result(x,photo_id="photo-one",input_run_ids=["unexpected"])
    def test_no_unanchored_change(self):
        x=sample()
        x["comparison"]["change"]="increased"
        with self.assertRaises(ValueError):
            validate_gemini_result(x,photo_id="photo-one",input_run_ids=x["input_run_ids"])
    def test_not_ground_truth(self):
        x=sample()
        x["clinical_accuracy_verified"]=True
        with self.assertRaises(ValueError):
            validate_gemini_result(x,photo_id="photo-one",input_run_ids=x["input_run_ids"])

if __name__=="__main__":
    unittest.main()
