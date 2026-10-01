import os
from supabase import create_client, Client
from models import NormalizedJob


def get_client() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


def upsert_job(client: Client, job: NormalizedJob) -> None:
    client.table("jobs").upsert(
        job.to_db(),
        on_conflict="fingerprint",
    ).execute()
