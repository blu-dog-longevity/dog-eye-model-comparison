import unittest
from dog_disease_validation import DOG_DISEASE_CLASSES, dog_disease_payload

def sample():
    scores = {k: .1/19 for k in DOG_DISEASE_CLASSES}
    scores["Ear infections"] = .9
    return {"model":"dog_disease_predictor","status":"ok",
            "prediction":"Ear infections","score":.9,"scores":scores}

class DogDiseaseTests(unittest.TestCase):
    def test_complete_scores_retained_without_claiming_eye_diagnosis(self):
        out = dog_disease_payload(sample(),run_id="r",dog_id="d")
        self.assertEqual(len(out["class_scores"]),20)
        self.assertEqual(out["assessment_status"],"unreviewed")
        self.assertEqual(out["predicted_label"],"Ear infections")
    def test_missing_category_rejected(self):
        x = sample()
        del x["scores"]["Lupus"]
        with self.assertRaises(ValueError):
            dog_disease_payload(x,run_id="r",dog_id="d")
    def test_wrong_model_rejected(self):
        x = sample()
        x["model"]="rady4"
        with self.assertRaises(ValueError):
            dog_disease_payload(x,run_id="r",dog_id="d")
    def test_invalid_score_rejected(self):
        x = sample()
        x["scores"]["Lupus"]=float("nan")
        with self.assertRaises(ValueError):
            dog_disease_payload(x,run_id="r",dog_id="d")

if __name__=="__main__":
    unittest.main()
