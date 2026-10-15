from sqlalchemy.orm import Session

from app.errors import ApiError
from app.members.schemas import MemberCreate, MemberOut, MemberUpdate
from app.pagination import Page, PageParams


def _todo() -> ApiError:
    return ApiError(501, "not_implemented", "Member operations are not implemented yet")


def create_member(session: Session, data: MemberCreate) -> MemberOut:
    raise _todo()


def list_members(session: Session, params: PageParams) -> Page[MemberOut]:
    raise _todo()


def get_member(session: Session, member_id: int) -> MemberOut:
    raise _todo()


def replace_member(session: Session, member_id: int, data: MemberCreate) -> MemberOut:
    raise _todo()


def update_member(session: Session, member_id: int, data: MemberUpdate) -> MemberOut:
    raise _todo()


def delete_member(session: Session, member_id: int) -> None:
    raise _todo()
