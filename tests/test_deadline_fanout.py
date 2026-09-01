from datetime import datetime, timezone

from course_fanout.delivery_service import fan_out_deadline
from course_fanout.models import CourseDelivery, LearnerSubscription


class RecordingQueue:
    def __init__(self) -> None:
        self.published: list[tuple[dict, str]] = []

    def publish(self, payload: dict, idempotency_key: str) -> str:
        self.published.append((payload, idempotency_key))
        return f"message-{len(self.published)}"


def test_fanout_skips_opted_out_learner_and_reports_delivery() -> None:
    delivery = CourseDelivery(
        course_id="biology-7",
        course_title="Cell Biology",
        deadline=datetime(2026, 9, 5, 16, tzinfo=timezone.utc),
        learners=[
            LearnerSubscription(
                learner_id="ada",
                channel="email",
                destination="ada@example.com",
            ),
            LearnerSubscription(
                learner_id="lin",
                channel="email",
                destination="lin@example.com",
                notifications_enabled=False,
            ),
        ],
    )
    queue = RecordingQueue()

    report = fan_out_deadline(
        delivery,
        queue,  # type: ignore[arg-type]
        now=datetime(2026, 9, 2, 9, tzinfo=timezone.utc),
    )

    assert report.model_dump() | {"deadline": report.deadline.isoformat()} == {
        "course_id": "biology-7",
        "deadline": "2026-09-05T16:00:00+00:00",
        "eligible": 1,
        "queued": 1,
        "skipped": 1,
        "message_ids": ["message-1"],
    }
    assert queue.published == [
        (
            {
                "event": "course.deadline",
                "course_id": "biology-7",
                "course_title": "Cell Biology",
                "learner_id": "ada",
                "channel": "email",
                "destination": "ada@example.com",
                "deadline": "2026-09-05T16:00:00+00:00",
                "days_remaining": 3,
            },
            "biology-7:2026-09-05T16:00:00+00:00:ada",
        )
    ]
