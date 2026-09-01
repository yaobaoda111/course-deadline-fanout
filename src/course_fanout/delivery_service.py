from datetime import datetime, timezone
from typing import Any, Protocol

from .models import CourseDelivery, EducatorReport


class QueuePublisher(Protocol):
    def publish(self, payload: dict[str, Any], idempotency_key: str) -> str: ...


def fan_out_deadline(
    delivery: CourseDelivery,
    queue: QueuePublisher,
    now: datetime | None = None,
) -> EducatorReport:
    observed_at = now or datetime.now(timezone.utc)
    deadline = delivery.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    active = [learner for learner in delivery.learners if learner.notifications_enabled]
    message_ids: list[str] = []
    for learner in active:
        payload = {
            "event": "course.deadline",
            "course_id": delivery.course_id,
            "course_title": delivery.course_title,
            "learner_id": learner.learner_id,
            "channel": learner.channel,
            "destination": learner.destination,
            "deadline": deadline.isoformat(),
            "days_remaining": max(0, (deadline.date() - observed_at.date()).days),
        }
        message_ids.append(
            queue.publish(
                payload=payload,
                idempotency_key=f"{delivery.course_id}:{deadline.isoformat()}:{learner.learner_id}",
            )
        )

    return EducatorReport(
        course_id=delivery.course_id,
        deadline=deadline,
        eligible=len(active),
        queued=len(message_ids),
        skipped=len(delivery.learners) - len(active),
        message_ids=message_ids,
    )
