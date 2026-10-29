"""Server-only Supabase PostgREST repository for the eye coordinator.

NOT a browser module. Only run in a trusted, isolated backend after checking
dog authorization. Credentials must be provided by a secret manager; never
commit them or expose them to Lovable/client bundles.

Requires the published Supabase project URL and a service-role secret at runtime.
The database unique attempt index is used to reject concurrent duplicates.
"""
from __future__ import annotations
import json
import os
from urllib import request

class BackendConfigError(RuntimeError):
    pass

class SupabaseRestRepository:
    def __init__(self, base_url: str, service_key: str, transport=None):
        if not base_url.startswith("https://") or not service_key:
            raise BackendConfigError("HTTPS Supabase URL and server-only key required")
        self.base_url = base_url.rstrip("/")
        self.service_key = service_key
        self.transport = transport or request.urlopen

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get("SUPABASE_URL", ""),
                   os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""))

    def _call(self, table, method="GET", payload=None, params=""):
        allowed = {"eye_model_runs", "eye_classifications", "eye_sam_measurements"}
        if table not in allowed:
            raise ValueError("Table not allowed by research writer")
        url = self.base_url + "/rest/v1/" + table + params
        body = json.dumps(payload, allow_nan=False).encode("utf-8") if payload is not None else None
        headers = {"apikey": self.service_key, "Authorization": "Bearer " + self.service_key,
                   "Accept": "application/json", "Content-Type": "application/json",
                   "Prefer": "return=representation"}
        req = request.Request(url, data=body, method=method, headers=headers)
        with self.transport(req) as response:
            return json.loads(response.read().decode("utf-8"))

    def find_run(self, photo_id, model_name, version, attempt):
        # Query JSON extraction through PostgREST; do not interpolate external user input.
        from urllib.parse import urlencode
        params = "?" + urlencode({"photo_id":"eq."+photo_id,"model_name":"eq."+model_name,
              "model_version":"eq."+version,"input_metadata->>attempt":"eq."+str(attempt),
              "select":"id,status,photo_id,dog_id,model_name,model_version,input_metadata","limit":"1"})
        rows = self._call("eye_model_runs", params=params)
        return rows[0] if rows else None

    def create_run(self, payload):
        rows = self._call("eye_model_runs", "POST", payload)
        return rows[0]

    def finish_run(self, run_id, payload):
        from urllib.parse import urlencode
        self._call("eye_model_runs", "PATCH", payload, "?"+urlencode({"id":"eq."+run_id}))

    def save_output(self, model_name, run_id, dog_id, output):
        # Only validated Rady model data can enter the classifications table.
        if model_name in ("rady4", "rady6"):
            try:
                from .supabase_payloads import classifier_payload
            except ImportError:
                from supabase_payloads import classifier_payload
            row = classifier_payload(row=output["source_row"], run_id=run_id, dog_id=dog_id)
            if row is None:
                raise ValueError("A completed Rady result requires valid classification")
            self._call("eye_classifications", "POST", row)
        elif model_name == "sam2_1":
            for item in output.get("measurements", []):
                try:
                    from .eye_output_validation import validate_sam_measurement
                except ImportError:
                    from eye_output_validation import validate_sam_measurement
                validate_sam_measurement(item)
                self._call("eye_sam_measurements", "POST",
                           {"model_run_id":run_id,"dog_id":dog_id, **item})
        elif model_name == "dog_disease_predictor":
            try:
                from .dog_disease_validation import dog_disease_payload
            except ImportError:
                from dog_disease_validation import dog_disease_payload
            row = dog_disease_payload(output["source_row"], run_id=run_id, dog_id=dog_id)
            self._call("eye_classifications", "POST", row)
        else:
            raise NotImplementedError("Gemini is handled by a separate synthesis worker")
