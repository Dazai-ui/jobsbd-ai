import os
import traceback

from classifier import accepted, enrich
from db import expire_past_deadlines, get_client, record_source_run, upsert_job
from fingerprint import make_fingerprint
from sources.registry import build_sources


def main():
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    include_demo = os.getenv("INCLUDE_DEMO", "false").lower() == "true"
    client = None if dry_run else get_client()

    if client is not None:
        expired_count = expire_past_deadlines(client)
        print(f"[cleanup] expired={expired_count}")

    sources = build_sources(include_demo=include_demo)
    total_accepted = 0
    failures = 0

    for source in sources:
        configure = getattr(source, "configure_runtime", None)
        if configure:
            configure(client)

        print(f"[source] {source.name}")
        discovered = 0
        accepted_count = 0

        try:
            for job in source.fetch():
                discovered += 1
                job = enrich(job)
                job.fingerprint = make_fingerprint(job)

                if not accepted(job):
                    continue

                accepted_count += 1
                total_accepted += 1
                print(
                    f"  accepted: {job.title} | {job.organization_name} "
                    f"| ai={job.is_ai_ml} academic={job.is_academic} "
                    f"| exp={job.experience_min}-{job.experience_max} "
                    f"| deadline={job.deadline} "
                    f"| priority={job.source_priority}"
                )

                if client is not None:
                    upsert_job(client, job)

            if client is not None:
                strategy = getattr(source, "active_strategy", None) or getattr(
                    source, "acquisition_strategy", "html"
                )
                record_source_run(
                    client,
                    source_name=source.name,
                    status="success",
                    discovered_count=discovered,
                    accepted_count=accepted_count,
                    strategy=strategy,
                )

            print(f"  done: discovered={discovered} accepted={accepted_count}")

        except Exception as exc:
            failures += 1
            print(f"  ERROR: {exc}")
            traceback.print_exc()

            if client is not None:
                strategy = getattr(source, "active_strategy", None) or getattr(
                    source, "acquisition_strategy", "html"
                )
                record_source_run(
                    client,
                    source_name=source.name,
                    status="failed",
                    discovered_count=discovered,
                    accepted_count=accepted_count,
                    error_message=str(exc)[:2000],
                    strategy=strategy,
                )

    print(f"[done] accepted={total_accepted} source_failures={failures}")

    if failures and failures == len(sources):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
