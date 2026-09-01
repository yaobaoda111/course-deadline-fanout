import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LearnerSubscription:
    learner_id: str
    channel: str
    destination: str
    notifications_enabled: bool = True


@dataclass
class CourseDelivery:
    course_id: str
    course_title: str
    deadline: datetime
    learners: list[LearnerSubscription]

    def __post_init__(self) -> None:
        if not self.learners:
            raise ValueError("learners must contain at least one subscription")


@dataclass
class EducatorReport:
    course_id: str
    deadline: datetime
    eligible: int
    queued: int
    skipped: int
    message_ids: list[str] = field(default_factory=list)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

    def model_dump_json(self, *, indent: int | None = None) -> str:
        return json.dumps(self.model_dump(), indent=indent, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
