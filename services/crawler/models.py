from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any

from source_policy import DISCOVERY_SOURCE_PRIORITY


@dataclass
class NormalizedJob:
    title: str
    organization_name: str
    source_name: str
    source_url: str

    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None

    description: Optional[str] = None
    requirements: Optional[str] = None
    skills: List[str] = field(default_factory=list)

    job_category: Optional[str] = None
    academic_role: Optional[str] = None

    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    freshers_allowed: bool = False

    is_ai_ml: bool = False
    is_academic: bool = False
    relevance_score: float = 0.0

    posted_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

    source_job_id: Optional[str] = None
    source_priority: int = DISCOVERY_SOURCE_PRIORITY
    raw_payload: Dict[str, Any] = field(default_factory=dict)

    fingerprint: Optional[str] = None

    def to_db(self) -> Dict[str, Any]:
        data = asdict(self)
        for field_name in ("posted_at", "deadline"):
            value = data.get(field_name)
            if value is not None:
                data[field_name] = value.isoformat()
        return data
