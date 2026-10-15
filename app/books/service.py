from sqlalchemy.orm import Session

from app.books.schemas import BookCreate, BookOut, BookUpdate
from app.errors import ApiError
from app.pagination import Page, PageParams


def _todo() -> ApiError:
    return ApiError(501, "not_implemented", "Book operations are not implemented yet")


def create_book(session: Session, data: BookCreate) -> BookOut:
    raise _todo()


def list_books(session: Session, q: str | None, params: PageParams) -> Page[BookOut]:
    raise _todo()


def get_book(session: Session, book_id: int) -> BookOut:
    raise _todo()


def replace_book(session: Session, book_id: int, data: BookCreate) -> BookOut:
    raise _todo()


def update_book(session: Session, book_id: int, data: BookUpdate) -> BookOut:
    raise _todo()


def delete_book(session: Session, book_id: int) -> None:
    raise _todo()
