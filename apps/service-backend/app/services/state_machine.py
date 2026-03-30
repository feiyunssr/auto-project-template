from app.core.errors import ServiceError
from app.models.enums import JobStatus

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    JobStatus.DRAFT.value: {JobStatus.QUEUED.value, JobStatus.CANCELLED.value},
    JobStatus.QUEUED.value: {JobStatus.RUNNING.value, JobStatus.CANCELLED.value},
    JobStatus.RUNNING.value: {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
        JobStatus.REVIEW_REQUIRED.value,
    },
    JobStatus.FAILED.value: {JobStatus.QUEUED.value, JobStatus.CANCELLED.value},
    JobStatus.REVIEW_REQUIRED.value: {JobStatus.QUEUED.value, JobStatus.CANCELLED.value},
    JobStatus.SUCCEEDED.value: {JobStatus.QUEUED.value},
    JobStatus.CANCELLED.value: set(),
}


def ensure_transition(current_status: str, target_status: str) -> None:
    if current_status == target_status:
        return
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise ServiceError(
            code="INVALID_STATUS_TRANSITION",
            message=f"Cannot transition job from {current_status} to {target_status}.",
            status_code=409,
        )
