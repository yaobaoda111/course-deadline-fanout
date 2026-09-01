from fastapi import FastAPI, HTTPException

from .delivery_service import fan_out_deadline
from .infrai_queue import InfraiError, InfraiQueue
from .models import CourseDelivery, EducatorReport

service = FastAPI(title="Course deadline fanout")


@service.post("/deliveries/fanout", response_model=EducatorReport)
def create_fanout(delivery: CourseDelivery) -> EducatorReport:
    try:
        return fan_out_deadline(delivery, InfraiQueue())
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
