from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.books.schemas import BookCreate, BookOut, BookUpdate
from app.counts import open_loans_for_book
from app.errors import ApiError
from app.models import Book, Loan
from app.pagination import Page, PageParams, paginate


def _out(session: Session, book: Book) -> BookOut:
    return BookOut(
        id=book.id,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        published_year=book.published_year,
        copies=book.copies,
        available_copies=book.copies - open_loans_for_book(session, book.id),
    )


def _load(session: Session, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise ApiError(404, "not_found", "Book not found")
    return book


def _duplicate() -> ApiError:
    return ApiError(409, "duplicate_isbn", "A book with this ISBN already exists")


def _check_isbn_free(session: Session, isbn: str, exclude_id: int | None = None) -> None:
    stmt = select(Book.id).where(Book.isbn == isbn)
    if exclude_id is not None:
        stmt = stmt.where(Book.id != exclude_id)
    if session.scalar(stmt) is not None:
        raise _duplicate()


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise _duplicate() from None


def create_book(session: Session, data: BookCreate) -> BookOut:
    _check_isbn_free(session, data.isbn)
    book = Book(**data.model_dump())
    session.add(book)
    _commit(session)
    session.refresh(book)
    return _out(session, book)


def list_books(session: Session, q: str | None, params: PageParams) -> Page[BookOut]:
    stmt = select(Book)
    if q:
        needle = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Book.title).like(needle), func.lower(Book.author).like(needle))
        )
    stmt = stmt.order_by(Book.title, Book.id)
    rows, total = paginate(session, stmt, params)
    return Page[BookOut](
        items=[_out(session, b) for b in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


def get_book(session: Session, book_id: int) -> BookOut:
    return _out(session, _load(session, book_id))


def _apply(session: Session, book: Book, values: dict) -> BookOut:
    if "isbn" in values:
        _check_isbn_free(session, values["isbn"], book.id)
    if "copies" in values and values["copies"] < open_loans_for_book(session, book.id):
        raise ApiError(
            409, "copies_below_open_loans", "copies cannot be lower than the number of open loans"
        )
    for key, value in values.items():
        setattr(book, key, value)
    _commit(session)
    session.refresh(book)
    return _out(session, book)


def replace_book(session: Session, book_id: int, data: BookCreate) -> BookOut:
    return _apply(session, _load(session, book_id), data.model_dump())


def update_book(session: Session, book_id: int, data: BookUpdate) -> BookOut:
    values = data.model_dump(exclude_unset=True, exclude_none=True)
    return _apply(session, _load(session, book_id), values)


def delete_book(session: Session, book_id: int) -> None:
    book = _load(session, book_id)
    if open_loans_for_book(session, book_id) > 0:
        raise ApiError(409, "has_open_loans", "Book has open loans")
    session.execute(delete(Loan).where(Loan.book_id == book_id))
    session.delete(book)
    session.commit()
