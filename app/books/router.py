from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.books import service
from app.books.schemas import BookCreate, BookOut, BookUpdate
from app.db import get_session
from app.errors import error_responses
from app.pagination import Page, PageParams
from app.security import WRITE_DEPENDENCIES

router = APIRouter(prefix="/books", tags=["books"])


@router.post(
    "",
    status_code=201,
    response_model=BookOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 409, 422, 503),
)
def create_book(data: BookCreate, session: Session = Depends(get_session)) -> BookOut:
    return service.create_book(session, data)


@router.get("", response_model=Page[BookOut], responses=error_responses(422))
def list_books(
    q: str | None = None,
    params: PageParams = Depends(),
    session: Session = Depends(get_session),
) -> Page[BookOut]:
    return service.list_books(session, q, params)


@router.get("/{book_id}", response_model=BookOut, responses=error_responses(404, 422))
def get_book(book_id: int, session: Session = Depends(get_session)) -> BookOut:
    return service.get_book(session, book_id)


@router.put(
    "/{book_id}",
    response_model=BookOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def replace_book(
    book_id: int, data: BookCreate, session: Session = Depends(get_session)
) -> BookOut:
    return service.replace_book(session, book_id, data)


@router.patch(
    "/{book_id}",
    response_model=BookOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def update_book(book_id: int, data: BookUpdate, session: Session = Depends(get_session)) -> BookOut:
    return service.update_book(session, book_id, data)


@router.delete(
    "/{book_id}",
    status_code=204,
    response_class=Response,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def delete_book(book_id: int, session: Session = Depends(get_session)) -> Response:
    service.delete_book(session, book_id)
    return Response(status_code=204)
