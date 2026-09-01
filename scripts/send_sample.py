from datetime import datetime, timedelta, timezone

from course_fanout.delivery_service import fan_out_deadline
from course_fanout.infrai_queue import InfraiQueue
from course_fanout.models import CourseDelivery, LearnerSubscription


delivery = CourseDelivery(
    course_id="python-101",
    course_title="Practical Python",
    deadline=datetime.now(timezone.utc) + timedelta(days=3),
    learners=[
        LearnerSubscription(
            learner_id="learner-17",
            channel="email",
            destination="learner17@example.com",
        ),
        LearnerSubscription(
            learner_id="learner-23",
            channel="email",
            destination="learner23@example.com",
        ),
    ],
)

print(fan_out_deadline(delivery, InfraiQueue()).model_dump_json(indent=2))
