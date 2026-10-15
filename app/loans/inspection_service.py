from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.errors import ApiError
from app.loans.schemas import LoanOut, OverdueLoanOut
from app.pagination import Page, PageParams


def _todo() -> ApiError:
    return ApiError(501, "not_implemented", "Loan inspection is not implemented yet")


def list_loans(
    session: Session,
    member_id: int | None,
    book_id: int | None,
    status: Literal["open", "returned", "all"],
    params: PageParams,
) -> Page[LoanOut]:
    raise _todo()


def list_overdue(session: Session, now: datetime, params: PageParams) -> Page[OverdueLoanOut]:
    raise _todo()


def get_loan(session: Session, loan_id: int) -> LoanOut:
    raise _todo()
