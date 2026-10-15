from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_session
from app.errors import ApiError, error_responses

router = APIRouter(tags=["health"])


@router.get("/health", responses=error_responses(503))
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ApiError(503, "internal_error", "Database unreachable") from exc
    return {"status": "ok"}
