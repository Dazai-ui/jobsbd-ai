import os
from datetime import datetime, timezone
from supabase import create_client, Client
from models import NormalizedJob


def get_client() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


def upsert_job(client: Client, job: NormalizedJob) -> None:
    now = datetime.now(timezone.utc).isoformat()
    payload = job.to_db()
    payload["last_seen_at"] = now

    result = client.table("jobs").upsert(
        payload,
        on_conflict="fingerprint",
    ).execute()

    rows = result.data or []
    if not rows:
        return

    job_id = rows[0]["id"]
    client.table("job_sources").upsert({
        "job_id": job_id,
        "source_name": job.source_name,
        "source_url": job.source_url,
        "source_job_id": job.source_job_id,
        "last_seen_at": now,
    }, on_conflict="job_id,source_url").execute()


def record_source_run(
    client: Client,
    *,
    source_name: str,
    status: str,
    discovered_count: int,
    accepted_count: int,
    error_message: str | None = None,
) -> None:
    client.table("source_runs").insert({
        "source_name": source_name,
        "status": status,
        "discovered_count": discovered_count,
        "accepted_count": accepted_count,
        "error_message": error_message,
    }).execute()
