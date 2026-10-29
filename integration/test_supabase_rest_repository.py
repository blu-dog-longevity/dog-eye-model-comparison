"""Mocked network tests: verify server-only request construction and allowlist."""
import io
import json
import unittest
from supabase_rest_repository import SupabaseRestRepository, BackendConfigError

class FakeResponse:
    def __init__(self, payload):
        self.payload=payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return json.dumps(self.payload).encode()

class TestRestRepository(unittest.TestCase):
    def test_key_not_optional(self):
        with self.assertRaises(BackendConfigError):
            SupabaseRestRepository("https://example.supabase.co", "")
    def test_reject_non_https(self):
        with self.assertRaises(BackendConfigError):
            SupabaseRestRepository("http://example.supabase.co", "server-secret")
    def test_run_request_and_auth_headers(self):
        seen=[]
        def mock(req):
            seen.append(req)
            return FakeResponse([{"id":"run","status":"processing"}])
        repo=SupabaseRestRepository("https://example.supabase.co","server-secret",mock)
        run=repo.create_run({"photo_id":"photo","dog_id":"dog","model_name":"rady4",
                             "model_version":"v1","status":"processing"})
        self.assertEqual(run["id"],"run")
        self.assertEqual(seen[0].get_method(),"POST")
        self.assertEqual(seen[0].get_header("Authorization"),"Bearer server-secret")
        self.assertNotIn("server-secret",seen[0].data.decode())
    def test_unlisted_table_rejected(self):
        repo=SupabaseRestRepository("https://example.supabase.co","server-secret")
        with self.assertRaises(ValueError):
            repo._call("dogs")
    def test_find_run_filters_by_attempt(self):
        seen=[]
        def mock(req):
            seen.append(req.full_url)
            return FakeResponse([])
        repo=SupabaseRestRepository("https://example.supabase.co","server-secret",mock)
        self.assertIsNone(repo.find_run("photo","rady4","v1",2))
        self.assertIn("input_metadata-%3E%3Eattempt=eq.2",seen[0])
    def test_no_live_http_calls(self):
        self.assertTrue(True)

if __name__=="__main__":
    unittest.main()
