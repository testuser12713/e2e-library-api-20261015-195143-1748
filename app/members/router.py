from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db import get_session
from app.errors import error_responses
from app.members import service
from app.members.schemas import MemberCreate, MemberOut, MemberUpdate
from app.pagination import Page, PageParams
from app.security import WRITE_DEPENDENCIES

router = APIRouter(prefix="/members", tags=["members"])


@router.post(
    "",
    status_code=201,
    response_model=MemberOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 409, 422, 503),
)
def create_member(data: MemberCreate, session: Session = Depends(get_session)) -> MemberOut:
    return service.create_member(session, data)


@router.get("", response_model=Page[MemberOut], responses=error_responses(422))
def list_members(
    params: PageParams = Depends(), session: Session = Depends(get_session)
) -> Page[MemberOut]:
    return service.list_members(session, params)


@router.get("/{member_id}", response_model=MemberOut, responses=error_responses(404, 422))
def get_member(member_id: int, session: Session = Depends(get_session)) -> MemberOut:
    return service.get_member(session, member_id)


@router.put(
    "/{member_id}",
    response_model=MemberOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def replace_member(
    member_id: int, data: MemberCreate, session: Session = Depends(get_session)
) -> MemberOut:
    return service.replace_member(session, member_id, data)


@router.patch(
    "/{member_id}",
    response_model=MemberOut,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def update_member(
    member_id: int, data: MemberUpdate, session: Session = Depends(get_session)
) -> MemberOut:
    return service.update_member(session, member_id, data)


@router.delete(
    "/{member_id}",
    status_code=204,
    response_class=Response,
    dependencies=WRITE_DEPENDENCIES,
    responses=error_responses(401, 404, 409, 422, 503),
)
def delete_member(member_id: int, session: Session = Depends(get_session)) -> Response:
    service.delete_member(session, member_id)
    return Response(status_code=204)
