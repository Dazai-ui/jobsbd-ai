import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from models import NormalizedJob


AI_KEYWORDS = {
    "artificial intelligence", "machine learning", "deep learning",
    "computer vision", "natural language processing", "nlp",
    "large language model", "llm", "generative ai", "genai",
    "data science", "data scientist", "ml engineer",
    "machine learning engineer", "ai engineer", "mlops",
    "research engineer", "pytorch", "tensorflow", "computer vision engineer",
    "data analyst", "data analytics", "business analytics"
}

ACADEMIC_ROLE_PATTERNS = {
    "assistant_lecturer": r"\bassistant\s+lecturer\b",
    "adjunct_lecturer": r"\badjunct\s+lecturer\b",
    "adjunct_faculty": r"\badjunct\s+faculty\b",
    "contractual_lecturer": r"\b(?:contractual|contract)\s+lecturer\b",
    "contractual_faculty": r"\b(?:contractual|contract)\s+faculty\b",
    "part_time_lecturer": r"\bpart[-\s]?time\s+lecturer\b",
    "visiting_lecturer": r"\bvisiting\s+lecturer\b",
    "visiting_faculty": r"\bvisiting\s+faculty\b",
    "research_assistant": r"\b(?:graduate\s+)?research\s+assistant\b",
    "teaching_assistant": r"\b(?:graduate\s+)?teaching\s+assistant\b",
    "faculty_member": r"\bfaculty\s+member\b",
    "lecturer": r"\blecturer\b",
}

NON_ENTRY_INDUSTRY_TITLE_RE = re.compile(
    r"\b(?:senior|sr\.?|lead|principal|manager|head|director|staff)\b",
    re.I,
)

NON_ENTRY_ACADEMIC_PATTERNS = (
    r"\bsenior\s+lecturer\b",
    r"\bassistant\s+professor\b",
    r"\bassociate\s+professor\b",
    r"\bprofessor\b",
    r"\bdean\b",
)

FRESHER_PATTERNS = (
    r"fresh(?:er|ers| graduate| graduates)",
    r"fresh graduates? (?:are )?(?:encouraged|welcome)",
    r"no experience required",
    r"experience not required",
    r"0\s*(?:-|–|to)\s*1\s*years?",
    r"0\s*(?:-|–|to)\s*2\s*years?",
)

EXPERIENCE_RANGE_RE = re.compile(
    r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*years?",
    re.I,
)
MIN_EXPERIENCE_RE = re.compile(
    r"(?:minimum|min\.?|at least)\s*(\d+(?:\.\d+)?)\s*years?",
    re.I,
)
SINGLE_EXPERIENCE_RE = re.compile(
    r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience",
    re.I,
)


def extract_experience(text: str) -> Tuple[Optional[float], Optional[float], bool]:
    lower = text.lower()
    fresh = any(re.search(p, lower, re.I) for p in FRESHER_PATTERNS)

    match = EXPERIENCE_RANGE_RE.search(lower)
    if match:
        return float(match.group(1)), float(match.group(2)), fresh

    match = MIN_EXPERIENCE_RE.search(lower)
    if match:
        value = float(match.group(1))
        return value, None, fresh

    match = SINGLE_EXPERIENCE_RE.search(lower)
    if match:
        value = float(match.group(1))
        return value, value, fresh

    if fresh:
        return 0.0, 0.0, True

    return None, None, False


def detect_academic_role(text: str) -> Optional[str]:
    lower = text.lower()

    for role, pattern in ACADEMIC_ROLE_PATTERNS.items():
        if role == "lecturer":
            continue
        if re.search(pattern, lower, re.I):
            return role

    if any(re.search(pattern, lower, re.I) for pattern in NON_ENTRY_ACADEMIC_PATTERNS):
        return None

    if re.search(ACADEMIC_ROLE_PATTERNS["lecturer"], lower, re.I):
        return "lecturer"

    return None


def enrich(job: NormalizedJob) -> NormalizedJob:
    text = " ".join(
        part for part in [
            job.title,
            job.department or "",
            job.description or "",
            job.requirements or "",
        ] if part
    )
    lower = text.lower()

    hits = [kw for kw in AI_KEYWORDS if kw in lower]
    job.is_ai_ml = len(hits) > 0

    role = detect_academic_role(text)
    job.academic_role = role
    job.is_academic = role is not None

    exp_min, exp_max, fresh = extract_experience(text)
    job.experience_min = job.experience_min if job.experience_min is not None else exp_min
    job.experience_max = job.experience_max if job.experience_max is not None else exp_max
    job.freshers_allowed = job.freshers_allowed or fresh

    score = 0.0
    if job.is_ai_ml:
        score += min(0.75, 0.15 * len(hits))
    if job.is_academic:
        score += 0.75
    if job.freshers_allowed:
        score += 0.20
    if job.experience_max is not None and job.experience_max <= 2:
        score += 0.20

    job.relevance_score = min(1.0, score)
    return job


def _expired(job: NormalizedJob) -> bool:
    if job.deadline is None:
        return False
    deadline = job.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline.date() < datetime.now(timezone.utc).date()


def accepted(job: NormalizedJob) -> bool:
    if _expired(job):
        return False

    if job.is_academic:
        if job.freshers_allowed:
            return True
        if job.experience_max is not None:
            return job.experience_max <= 2
        if job.experience_min is not None:
            return job.experience_min <= 2
        return True

    if not job.is_ai_ml:
        return False

    if job.freshers_allowed:
        return True

    if job.experience_max is not None:
        return job.experience_max <= 2

    if job.experience_min is not None:
        return job.experience_min <= 2

    if NON_ENTRY_INDUSTRY_TITLE_RE.search(job.title):
        return False

    return True
