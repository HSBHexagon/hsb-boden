"""Cloud Storage generation-precondition singleton lock for scheduled draft workers.

Includes automatic stale-lock expiration (TTL = 15 minutes) to recover from hard crashes.
An active lock acquisition guarantees exactly-one running worker across Cloud Run executions.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import time


@contextmanager
def singleton_cloud_lock(bucket_name: str, storage_client=None, ttl_seconds: int = 900):
    if not bucket_name:
        raise ValueError("Cloud lock bucket is mandatory")
    if storage_client is None:
        from google.cloud import storage
        storage_client = storage.Client()
    from google.api_core.exceptions import PreconditionFailed

    blob = storage_client.bucket(bucket_name).blob("hsb-com-drafts/worker.lock")
    now_ts = time.time()
    lock_payload = json.dumps({
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": now_ts,
        "message": "HSB COM draft dispatcher active"
    })

    acquired = False
    try:
        # 1. Clean acquire: succeeds only if object does not exist yet (generation 0)
        blob.upload_from_string(
            lock_payload,
            content_type="application/json",
            if_generation_match=0
        )
        acquired = True
    except PreconditionFailed:
        # 2. Lock already exists: check for stale lock expiration (> ttl_seconds)
        try:
            blob.reload()
            curr_generation = blob.generation
            content = blob.download_as_text()
            data = json.loads(content) if content.strip().startswith("{") else {}
            lock_ts = data.get("timestamp", 0)
            if now_ts - lock_ts > ttl_seconds and curr_generation is not None:
                # Stale lock: atomically overwrite with generation-precondition
                blob.upload_from_string(
                    lock_payload,
                    content_type="application/json",
                    if_generation_match=curr_generation
                )
                acquired = True
            else:
                yield False
                return
        except Exception:
            yield False
            return

    try:
        yield acquired
    finally:
        # Atomic release: only delete if the generation matches what we uploaded
        if acquired and blob.generation is not None:
            try:
                blob.delete(if_generation_match=blob.generation)
            except Exception:
                pass
