"""Isolated MEtech eye analysis coordinator.

Runnable with injected model workers and repository implementation.
Does not run actual ML inference or connect to Supabase by itself.
A trusted backend must authorize the dog/photo before calling this module.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Protocol, Any
from uuid import uuid4

MODELS = ("rady4", "rady6", "dog_disease_predictor", "sam2_1")
TERMINAL = frozenset(("completed", "failed", "skipped"))


class RunRepository(Protocol):
    def find_run(self, photo_id: str, model_name: str, version: str, attempt: int) -> dict | None: ...
    def create_run(self, payload: dict) -> dict: ...
    def finish_run(self, run_id: str, payload: dict) -> None: ...
    def save_output(self, model_name: str, run_id: str, dog_id: str, output: dict) -> None: ...


@dataclass(frozen=True)
class Job:
    photo_id: str
    dog_id: str
    private_image_reference: str
    versions: dict[str, str]
    attempt: int = 1

    def __post_init__(self):
        if not self.photo_id or not self.dog_id or not self.private_image_reference:
            raise ValueError("Photo, dog, and private image reference are required")
        if self.attempt < 1 or any(not self.versions.get(name) for name in MODELS):
            raise ValueError("Version per model and positive attempt are required")


def process_photo(job: Job, repository: RunRepository,
                  workers: dict[str, Callable[[Job], dict[str, Any]]]) -> dict[str, str]:
    """Persist each model independently; retries create new attempt-specific runs.

    Injection lets research jobs run offline. Caller guarantees authorization,
    run idempotency with database uniqueness/locking, and trusted worker versions.
    """
    result = {}
    for name in MODELS:
        version = job.versions[name]
        prior = repository.find_run(job.photo_id, name, version, job.attempt)
        if prior:
            result[name] = prior["status"]
            continue
        run = repository.create_run({
            "id": str(uuid4()), "photo_id": job.photo_id, "dog_id": job.dog_id,
            "model_name": name, "model_version": version,
            "run_kind": "inference", "status": "processing",
            "input_metadata": {"attempt": job.attempt},
        })
        try:
            worker = workers.get(name)
            if worker is None:
                repository.finish_run(run["id"], {"status": "skipped", "error_code": "worker_not_configured"})
                result[name] = "skipped"
                continue
            output = worker(job)
            if not isinstance(output, dict):
                raise ValueError("Worker must return a result dictionary")
            status = output.get("status")
            if status not in ("completed", "skipped"):
                raise ValueError("Worker returned an invalid terminal state")
            if status == "completed":
                repository.save_output(name, run["id"], job.dog_id, output)
            repository.finish_run(run["id"], {"status": status, "output_metadata": {"worker_state": status}})
            result[name] = status
        except Exception as exc:
            # Never store raw exceptions: they can contain private URLs or image paths.
            repository.finish_run(run["id"], {"status": "failed", "error_code": "worker_execution_failed"})
            result[name] = "failed"
    return result
