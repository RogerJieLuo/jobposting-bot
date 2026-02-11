from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Job:
    id: str
    title: str
    url: str
    company: str
    location: str

    applicants: Optional[int] = None
    description: Optional[str] = None
    decision: Optional[str] = None
    reason: Optional[str] = None

    fetched_at: datetime = field(default_factory=datetime.utcnow)
