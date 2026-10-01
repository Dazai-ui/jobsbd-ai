import os

from db import get_client, upsert_job
from pipeline import process
from sources.demo_source import DemoSource


def main():
    sources = [DemoSource()]
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    client = None if dry_run else get_client()
    total = 0

    for source in sources:
        print(f"[source] {source.name}")
        for job in process(source.fetch()):
            total += 1
            print(
                f"  accepted: {job.title} | {job.organization_name} "
                f"| ai={job.is_ai_ml} academic={job.is_academic} "
                f"| exp={job.experience_min}-{job.experience_max}"
            )
            if client is not None:
                upsert_job(client, job)

    print(f"[done] accepted {total} jobs")


if __name__ == "__main__":
    main()
