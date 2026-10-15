from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.counts import open_loans_for_book, open_loans_for_member
from app.errors import ApiError
from app.loans.schemas import LoanCreate, LoanOut
from app.models import Book, Loan, Member

LOAN_DAYS = 14
MAX_OPEN_LOANS = 3


def _not_found() -> ApiError:
    return ApiError(404, "not_found", "Resource not found")


def create_loan(session: Session, data: LoanCreate, now: datetime) -> LoanOut:
    if session.in_transaction():
        session.rollback()
    # A write first makes SQLite take its lock, so checks and insert are atomic.
    session.execute(text("UPDATE loans SET id = id WHERE 0"))
    book = session.get(Book, data.book_id)
    member = session.get(Member, data.member_id)
    if book is None or member is None:
        session.rollback()
        raise _not_found()
    if open_loans_for_book(session, book.id) >= book.copies:
        session.rollback()
        raise ApiError(409, "no_copy_available", "No free copy of this book")
    if open_loans_for_member(session, member.id) >= MAX_OPEN_LOANS:
        session.rollback()
        raise ApiError(409, "loan_limit_reached", "Member has reached the loan limit")
    loan = Loan(
        book_id=book.id,
        member_id=member.id,
        loaned_at=now,
        due_at=now + timedelta(days=LOAN_DAYS),
    )
    session.add(loan)
    session.commit()
    return LoanOut.model_validate(loan)


def return_loan(session: Session, loan_id: int, now: datetime) -> LoanOut:
    loan = session.get(Loan, loan_id)
    if loan is None:
        raise _not_found()
    if loan.returned_at is not None:
        raise ApiError(409, "already_returned", "Loan was already returned")
    loan.returned_at = now
    session.commit()
    return LoanOut.model_validate(loan)
