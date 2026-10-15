from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.loans.schemas import LoanOut, OverdueLoanOut
from app.models import Loan
from app.pagination import Page, PageParams, paginate


def list_loans(
    session: Session,
    member_id: int | None,
    book_id: int | None,
    status: Literal["open", "returned", "all"],
    params: PageParams,
) -> Page[LoanOut]:
    stmt = select(Loan)
    if member_id is not None:
        stmt = stmt.where(Loan.member_id == member_id)
    if book_id is not None:
        stmt = stmt.where(Loan.book_id == book_id)
    if status == "open":
        stmt = stmt.where(Loan.returned_at.is_(None))
    elif status == "returned":
        stmt = stmt.where(Loan.returned_at.is_not(None))
    rows, total = paginate(session, stmt.order_by(Loan.loaned_at, Loan.id), params)
    return Page[LoanOut](
        items=[LoanOut.model_validate(r) for r in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


def list_overdue(session: Session, now: datetime, params: PageParams) -> Page[OverdueLoanOut]:
    stmt = (
        select(Loan)
        .where(Loan.returned_at.is_(None), Loan.due_at < now)
        .order_by(Loan.due_at, Loan.id)
    )
    rows, total = paginate(session, stmt, params)
    items = [
        OverdueLoanOut(
            **LoanOut.model_validate(r).model_dump(),
            days_overdue=(now - r.due_at).days,
        )
        for r in rows
    ]
    return Page[OverdueLoanOut](items=items, total=total, limit=params.limit, offset=params.offset)


def get_loan(session: Session, loan_id: int) -> LoanOut:
    loan = session.get(Loan, loan_id)
    if loan is None:
        raise ApiError(404, "not_found", f"Loan {loan_id} not found")
    return LoanOut.model_validate(loan)
