import unittest
from eye_coordinator import Job, MODELS, process_photo

class MemoryRepository:
    def __init__(self):
        self.runs=[]
        self.outputs=[]
    def find_run(self, photo_id, model_name, version, attempt):
        return next((r for r in self.runs if r["photo_id"]==photo_id and r["model_name"]==model_name and
                     r["model_version"]==version and r["input_metadata"]["attempt"]==attempt),None)
    def create_run(self, payload):
        self.runs.append(payload)
        return payload
    def finish_run(self, run_id, payload):
        run=next(r for r in self.runs if r["id"]==run_id)
        run.update(payload)
    def save_output(self, model_name, run_id, dog_id, output):
        self.outputs.append((model_name,run_id,dog_id,output))

def job(attempt=1):
    return Job("photo-1","dog-1","private://image",dict.fromkeys(MODELS,"test-v1"),attempt)

class CoordinatorTests(unittest.TestCase):
    def test_independent_failure_and_missing_worker(self):
        r=MemoryRepository()
        def failure(_job): raise RuntimeError("sensitive private path")
        result=process_photo(job(),r,{"rady4":lambda _:{"status":"completed","scores":{}},
                                     "rady6":failure})
        self.assertEqual(result,{"rady4":"completed","rady6":"failed",
                                 "dog_disease_predictor":"skipped","sam2_1":"skipped"})
        self.assertEqual(len(r.outputs),1)
        self.assertEqual(r.runs[1]["error_code"],"worker_execution_failed")
        self.assertNotIn("private path",str(r.runs))
    def test_same_attempt_is_idempotent_sequentially(self):
        r=MemoryRepository()
        process_photo(job(),r,{})
        process_photo(job(),r,{})
        self.assertEqual(len(r.runs),4)
    def test_new_attempt_creates_new_runs(self):
        r=MemoryRepository()
        process_photo(job(1),r,{})
        process_photo(job(2),r,{})
        self.assertEqual(len(r.runs),8)
    def test_missing_version_rejected(self):
        with self.assertRaises(ValueError):
            Job("p","d","image",{"rady4":"v1"})
    def test_bad_worker_output_is_failed(self):
        r=MemoryRepository()
        state=process_photo(job(),r,{"rady4":lambda _:{"status":"unknown"}})
        self.assertEqual(state["rady4"],"failed")

if __name__=="__main__":
    unittest.main()
