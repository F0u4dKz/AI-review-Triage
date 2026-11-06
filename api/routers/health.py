from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: Literal["ok"]


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    return HealthStatus(status="ok")
