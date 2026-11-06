from fastapi import APIRouter, Depends, HTTPException, status

from api.config import Settings
from api.dependencies import get_settings, require_api_key
from api.schemas.review import ReviewAccepted, ReviewIn
from api.services.inbox import DuplicateReviewError, UnsafeReviewIdError, accept_review

router = APIRouter(tags=["reviews"], dependencies=[Depends(require_api_key)])


@router.post(
    "/webhook/reviews",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReviewAccepted,
    responses={
        401: {"description": "Missing or invalid API key"},
        409: {"description": "A review with this review_id was already accepted"},
        422: {"description": "Payload failed validation"},
    },
)
def receive_review(review: ReviewIn, settings: Settings = Depends(get_settings)) -> ReviewAccepted:
    try:
        accept_review(review, settings.landing_dir)
    except DuplicateReviewError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="duplicate review_id")
    except UnsafeReviewIdError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid review_id")
    return ReviewAccepted(review_id=review.review_id)
