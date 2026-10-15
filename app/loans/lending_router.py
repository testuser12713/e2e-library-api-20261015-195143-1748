from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clock import get_now
from app.db import get_session
from app.errors import error_responses
from app.loans import lending_service
from app.loans.schemas import LoanCreate, LoanOut
from app.security import WRITE_DEPENDENCIES

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post(
    "",
    status_code=201,
    response_model=LoanOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def create_loan(
    data: LoanCreate,
    session: Session = Depends(get_session),
    now: datetime = Depends(get_now),
) -> LoanOut:
    return lending_service.create_loan(session, data, now)


@router.post(
    "/{loan_id}/return",
    response_model=LoanOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def return_loan(
    loan_id: int,
    session: Session = Depends(get_session),
    now: datetime = Depends(get_now),
) -> LoanOut:
    return lending_service.return_loan(session, loan_id, now)
