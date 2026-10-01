import hashlib
import re
from models import NormalizedJob


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\bltd\.?\b", "limited", text)
    text = re.sub(r"\bplc\.?\b", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_fingerprint(job: NormalizedJob) -> str:
    """Create a source-independent duplicate key.

    Prefer employer/title/location plus a real vacancy date when available,
    so the same posting discovered on multiple portals collapses into one job.
    """
    date_key = ""
    if job.deadline:
        date_key = job.deadline.date().isoformat()
    elif job.posted_at:
        date_key = job.posted_at.date().isoformat()

    canonical = "|".join([
        normalize(job.organization_name),
        normalize(job.title),
        normalize(job.location or ""),
        date_key,
    ])
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
