import os
from dataclasses import asdict
from typing import Any

import requests

from models import NormalizedJob


class IngestClient:
    def __init__(self, endpoint: str, token: str):
        self.endpoint = endpoint.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "JobsBDAggregator/0.4",
        })

    def post(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(self.endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("error") or "Ingest request failed")
        return data


def get_client() -> IngestClient:
    endpoint = os.environ["INGEST_ENDPOINT"]
    token = os.environ["INGEST_OIDC_TOKEN"]
    return IngestClient(endpoint, token)


def _serialize_job(job: NormalizedJob) -> dict[str, Any]:
    payload = asdict(job)
    for key in ("posted_at", "deadline"):
        value = payload.get(key)
        if value is not None:
            payload[key] = value.isoformat()
    return payload


def upsert_job(client: IngestClient, job: NormalizedJob) -> None:
    client.post({
        "action": "upsert_job",
        "job": _serialize_job(job),
    })


def expire_past_deadlines(client: IngestClient) -> int:
    data = client.post({"action": "expire_past_deadlines"})
    return int(data.get("expired", 0))


def record_source_run(
    client: IngestClient,
    *,
    source_name: str,
    status: str,
    discovered_count: int,
    accepted_count: int,
    error_message: str | None = None,
    strategy: str | None = None,
) -> None:
    client.post({
        "action": "record_source_run",
        "source_name": source_name,
        "status": status,
        "discovered_count": discovered_count,
        "accepted_count": accepted_count,
        "error_message": error_message,
        "strategy": strategy,
    })


def get_source_state(
    client: IngestClient,
    *,
    source_name: str,
    url: str,
    strategy: str = "html",
) -> dict[str, Any] | None:
    data = client.post({
        "action": "get_source_state",
        "source_name": source_name,
        "url": url,
        "strategy": strategy,
    })
    return data.get("state")


def upsert_source_state(
    client: IngestClient,
    *,
    source_name: str,
    url: str,
    strategy: str,
    etag: str | None,
    last_modified: str | None,
    content_hash: str | None,
    last_http_status: int | None,
    changed: bool,
    last_changed_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    client.post({
        "action": "upsert_source_state",
        "state": {
            "source_name": source_name,
            "url": url,
            "strategy": strategy,
            "etag": etag,
            "last_modified": last_modified,
            "content_hash": content_hash,
            "last_http_status": last_http_status,
            "changed": changed,
            "last_changed_at": last_changed_at,
            "metadata": metadata or {},
        },
    })
