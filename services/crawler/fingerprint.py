import hashlib
import re
from models import NormalizedJob


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\bltd\.?\b", "limited", text)
    text = re.sub(r"\s+", " ", text)
    return text


def make_fingerprint(job: NormalizedJob) -> str:
    deadline = job.deadline.date().isoformat() if job.deadline else ""
    source_id = job.source_job_id or ""
    canonical = "|".join([
        normalize(job.organization_name),
        normalize(job.title),
        deadline,
        source_id,
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
