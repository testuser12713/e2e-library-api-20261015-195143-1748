from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.counts import open_loans_for_member
from app.errors import ApiError
from app.members.schemas import MemberCreate, MemberOut, MemberUpdate
from app.models import Loan, Member
from app.pagination import Page, PageParams, paginate


def _out(session: Session, m: Member) -> MemberOut:
    return MemberOut(
        id=m.id,
        name=m.name,
        email=m.email,
        member_since=m.member_since,
        open_loans=open_loans_for_member(session, m.id),
    )


def _load(session: Session, member_id: int) -> Member:
    m = session.get(Member, member_id)
    if m is None:
        raise ApiError(404, "not_found", f"Member {member_id} not found")
    return m


def _check_email(session: Session, email: str, exclude_id: int | None = None) -> None:
    stmt = select(Member.id).where(func.lower(Member.email) == email.lower())
    if exclude_id is not None:
        stmt = stmt.where(Member.id != exclude_id)
    if session.scalar(stmt) is not None:
        raise ApiError(409, "duplicate_email", "A member with this e-mail already exists")


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ApiError(409, "duplicate_email", "A member with this e-mail already exists") from None


def create_member(session: Session, data: MemberCreate, now: datetime) -> MemberOut:
    _check_email(session, data.email)
    m = Member(
        name=data.name,
        email=data.email.lower(),
        member_since=data.member_since or now.date(),
    )
    session.add(m)
    _commit(session)
    return _out(session, m)


def list_members(session: Session, params: PageParams) -> Page[MemberOut]:
    rows, total = paginate(session, select(Member).order_by(Member.name, Member.id), params)
    return Page[MemberOut](
        items=[_out(session, m) for m in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


def get_member(session: Session, member_id: int) -> MemberOut:
    return _out(session, _load(session, member_id))


def replace_member(session: Session, member_id: int, data: MemberCreate) -> MemberOut:
    m = _load(session, member_id)
    _check_email(session, data.email, member_id)
    m.name = data.name
    m.email = data.email.lower()
    if data.member_since is not None:
        m.member_since = data.member_since
    _commit(session)
    return _out(session, m)


def update_member(session: Session, member_id: int, data: MemberUpdate) -> MemberOut:
    m = _load(session, member_id)
    fields = data.model_dump(exclude_unset=True)
    if fields.get("email") is not None:
        _check_email(session, fields["email"], member_id)
        m.email = fields["email"].lower()
    if fields.get("name") is not None:
        m.name = fields["name"]
    if fields.get("member_since") is not None:
        m.member_since = fields["member_since"]
    _commit(session)
    return _out(session, m)


def delete_member(session: Session, member_id: int) -> None:
    m = _load(session, member_id)
    if open_loans_for_member(session, member_id) > 0:
        raise ApiError(409, "has_open_loans", "Member has open loans")
    for loan in session.scalars(select(Loan).where(Loan.member_id == member_id)):
        session.delete(loan)
    session.delete(m)
    session.commit()
