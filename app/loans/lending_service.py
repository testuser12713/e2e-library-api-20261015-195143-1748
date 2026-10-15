from datetime import datetime

from sqlalchemy.orm import Session

from app.errors import ApiError
from app.loans.schemas import LoanCreate, LoanOut


def _todo() -> ApiError:
    return ApiError(501, "not_implemented", "Lending is not implemented yet")


def create_loan(session: Session, data: LoanCreate, now: datetime) -> LoanOut:
    raise _todo()


def return_loan(session: Session, loan_id: int, now: datetime) -> LoanOut:
    raise _todo()
