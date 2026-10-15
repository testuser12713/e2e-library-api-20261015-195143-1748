from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clock import get_now
from app.db import get_session
from app.errors import error_responses
from app.loans import inspection_service
from app.loans.schemas import LoanOut, OverdueLoanOut
from app.pagination import Page, PageParams

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("", response_model=Page[LoanOut], responses=error_responses(422))
def list_loans(
    member_id: int | None = None,
    book_id: int | None = None,
    status: Literal["open", "returned", "all"] = "all",
    params: PageParams = Depends(),
    session: Session = Depends(get_session),
) -> Page[LoanOut]:
    return inspection_service.list_loans(session, member_id, book_id, status, params)


# Must stay registered before "/{loan_id}" so "overdue" is not parsed as an id.
@router.get("/overdue", response_model=Page[OverdueLoanOut], responses=error_responses(422))
def list_overdue(
    params: PageParams = Depends(),
    session: Session = Depends(get_session),
    now: datetime = Depends(get_now),
) -> Page[OverdueLoanOut]:
    return inspection_service.list_overdue(session, now, params)


@router.get("/{loan_id}", response_model=LoanOut, responses=error_responses(404, 422))
def get_loan(loan_id: int, session: Session = Depends(get_session)) -> LoanOut:
    return inspection_service.get_loan(session, loan_id)
