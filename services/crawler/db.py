import os
from datetime import datetime, timezone

from supabase import Client, create_client

from models import NormalizedJob
from source_policy import should_replace_primary


def get_client() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


def upsert_job(client: Client, job: NormalizedJob) -> None:
    now = datetime.now(timezone.utc).isoformat()
    payload = job.to_db()
    payload["last_seen_at"] = now

    existing_result = (
        client.table("jobs")
        .select("id,source_priority")
        .eq("fingerprint", job.fingerprint)
        .limit(1)
        .execute()
    )
    existing_rows = existing_result.data or []

    if existing_rows:
        existing = existing_rows[0]
        job_id = existing["id"]

        if should_replace_primary(
            existing.get("source_priority"),
            job.source_priority,
        ):
            payload["updated_at"] = now
            client.table("jobs").update(payload).eq("id", job_id).execute()
        else:
            client.table("jobs").update({
                "last_seen_at": now,
            }).eq("id", job_id).execute()
    else:
        result = client.table("jobs").insert(payload).execute()
        rows = result.data or []
        if not rows:
            return
        job_id = rows[0]["id"]

    client.table("job_sources").upsert({
        "job_id": job_id,
        "source_name": job.source_name,
        "source_url": job.source_url,
        "source_job_id": job.source_job_id,
        "source_priority": job.source_priority,
        "last_seen_at": now,
    }, on_conflict="job_id,source_url").execute()


def expire_past_deadlines(client: Client) -> int:
    now = datetime.now(timezone.utc).isoformat()
    result = (
        client.table("jobs")
        .update({
            "status": "expired",
            "updated_at": now,
        })
        .eq("status", "active")
        .lt("deadline", now)
        .execute()
    )
    return len(result.data or [])


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
