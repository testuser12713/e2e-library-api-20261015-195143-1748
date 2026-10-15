from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Loan


def open_loans_for_book(session: Session, book_id: int) -> int:
    stmt = select(func.count(Loan.id)).where(Loan.book_id == book_id, Loan.returned_at.is_(None))
    return session.scalar(stmt) or 0


def open_loans_for_member(session: Session, member_id: int) -> int:
    stmt = select(func.count(Loan.id)).where(
        Loan.member_id == member_id, Loan.returned_at.is_(None)
    )
    return session.scalar(stmt) or 0
