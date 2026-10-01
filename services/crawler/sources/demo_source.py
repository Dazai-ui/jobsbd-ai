from datetime import datetime, timedelta, timezone
from typing import Iterable

from base import JobSource
from models import NormalizedJob
from source_policy import DEMO_SOURCE_PRIORITY


class DemoSource(JobSource):
    name = "Demo Source"

    def fetch(self) -> Iterable[NormalizedJob]:
        now = datetime.now(timezone.utc)

        yield NormalizedJob(
            title="Junior Machine Learning Engineer",
            organization_name="Demo AI Company",
            source_name=self.name,
            source_url="https://example.com/jobs/junior-ml-engineer",
            location="Dhaka",
            employment_type="Full-time",
            description=(
                "Work on machine learning and computer vision products. "
                "Fresh graduates are encouraged to apply."
            ),
            requirements="Python, PyTorch, 0-2 years of experience.",
            skills=["Python", "PyTorch", "Computer Vision"],
            posted_at=now,
            deadline=now + timedelta(days=21),
            source_job_id="demo-ml-001",
            source_priority=DEMO_SOURCE_PRIORITY,
            raw_payload={"demo": True},
        )

        yield NormalizedJob(
            title="Lecturer, Department of CSE",
            organization_name="Demo University",
            source_name=self.name,
            source_url="https://example.edu/careers/lecturer-cse",
            department="CSE",
            location="Dhaka",
            employment_type="Full-time",
            description="University-level Lecturer position in the Department of CSE.",
            requirements="Fresh graduates may apply. Teaching experience is not required.",
            posted_at=now,
            deadline=now + timedelta(days=14),
            source_job_id="demo-academic-001",
            source_priority=DEMO_SOURCE_PRIORITY,
            raw_payload={"demo": True},
        )

        # This should be rejected by the entry-level filter.
        yield NormalizedJob(
            title="Senior AI Engineer",
            organization_name="Demo AI Company",
            source_name=self.name,
            source_url="https://example.com/jobs/senior-ai-engineer",
            location="Dhaka",
            description="Artificial intelligence engineering role.",
            requirements="Minimum 5 years of experience.",
            posted_at=now,
            source_job_id="demo-senior-001",
            source_priority=DEMO_SOURCE_PRIORITY,
            raw_payload={"demo": True},
        )
