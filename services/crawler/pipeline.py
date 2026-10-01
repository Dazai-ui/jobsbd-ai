from typing import Iterable
from classifier import enrich, accepted
from fingerprint import make_fingerprint
from models import NormalizedJob


def process(jobs: Iterable[NormalizedJob]):
    for job in jobs:
        job = enrich(job)
        job.fingerprint = make_fingerprint(job)
        if accepted(job):
            yield job
