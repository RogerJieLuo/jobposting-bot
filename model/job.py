from dataclasses import dataclass
from typing import Optional


@dataclass
class Job:
    id: str
    title: str
    url: str
    company: str
    location: str
    """Country key for per-country config (e.g. 'canada', 'us', 'japan'). Used for prompts and Slack template."""
    country: Optional[str] = None

    applicants: Optional[int] = None
    description: Optional[str] = None
    decision: Optional[str] = None
    reason: Optional[str] = None
