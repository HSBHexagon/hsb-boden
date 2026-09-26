#!/usr/bin/env python3
"""
Microsoft Graph $batch Execution Engine for HSB Sales OS.
Executes up to 20 REST operations in a single HTTP roundtrip to https://graph.microsoft.com/v1.0/$batch.
Reduces network roundtrips by ~95% and accelerates bulk draft management (1.000+ items).
"""
import sys
import json
import time
import requests
from typing import List, Dict, Any, Optional

GRAPH_BATCH_ENDPOINT = "https://graph.microsoft.com/v1.0/$batch"
MAX_BATCH_SIZE = 20  # Microsoft Graph hard limit per $batch call

class GraphBatchEngine:
    def __init__(self, access_token: str, max_retries: int = 3):
        self.access_token = access_token
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def execute_batch(self, sub_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a single batch of up to 20 sub-requests.
        Handles 429 throttling and retry-after.
        """
        if len(sub_requests) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size exceeds Microsoft Graph limit of {MAX_BATCH_SIZE} (got {len(sub_requests)})")

        payload = {"requests": sub_requests}
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(GRAPH_BATCH_ENDPOINT, json=payload, timeout=30)
                
                # Check for rate limiting / throttling (HTTP 429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                    print(f"[GraphBatch] Rate limited (429). Retrying in {retry_after}s (attempt {attempt}/{self.max_retries})...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()
                
                # Parse responses into a lookup map {id: response_dict}
                responses_map = {}
                for resp in data.get("responses", []):
                    resp_id = resp.get("id")
                    status = resp.get("status")
                    if status == 429:
                        # Sub-request throttled
                        pass
                    responses_map[resp_id] = resp
                return responses_map

            except requests.exceptions.RequestException as e:
                print(f"[GraphBatch] Request error on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    raise
                time.sleep(2 ** attempt)

        return {}

    def execute_all(self, all_requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Chunks an arbitrary list of sub-requests into 20-item batches and executes sequentially.
        """
        results = {}
        total = len(all_requests)
        for i in range(0, total, MAX_BATCH_SIZE):
            chunk = all_requests[i:i + MAX_BATCH_SIZE]
            print(f"[GraphBatch] Dispatching batch {i//MAX_BATCH_SIZE + 1} ({len(chunk)} requests)...")
            batch_result = self.execute_batch(chunk)
            results.update(batch_result)
            time.sleep(0.2)  # Mild pacing to prevent burst 429s
        return results

    @staticmethod
    def build_delete_request(req_id: str, message_id: str) -> Dict[str, Any]:
        return {
            "id": req_id,
            "method": "DELETE",
            "url": f"/me/messages/{message_id}"
        }

    @staticmethod
    def build_get_draft_request(req_id: str, message_id: str) -> Dict[str, Any]:
        return {
            "id": req_id,
            "method": "GET",
            "url": f"/me/messages/{message_id}?$select=id,subject,toRecipients,hasAttachments,createdDateTime"
        }

    @staticmethod
    def build_create_draft_request(req_id: str, subject: str, to_email: str, body_html: str) -> Dict[str, Any]:
        return {
            "id": req_id,
            "method": "POST",
            "url": "/me/messages",
            "headers": {"Content-Type": "application/json"},
            "body": {
                "subject": subject,
                "importance": "Normal",
                "toRecipients": [{"emailAddress": {"address": to_email}}],
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                }
            }
        }

if __name__ == "__main__":
    print("GraphBatchEngine initialized. Usage: import in mailbox overhaul engines.")
