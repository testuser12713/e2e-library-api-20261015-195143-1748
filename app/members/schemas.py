from datetime import UTC, date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def _not_future(v: date | None) -> date | None:
    if v is not None and v > datetime.now(UTC).date():
        raise ValueError("member_since must not be in the future")
    return v


def _lower(v: str | None) -> str | None:
    return v.lower() if v is not None else None


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    member_since: date | None = None

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str | None) -> str | None:
        return _lower(v)

    @field_validator("member_since")
    @classmethod
    def _since_not_future(cls, v: date | None) -> date | None:
        return _not_future(v)


class MemberUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    email: EmailStr | None = None
    member_since: date | None = None

    @field_validator("email")
    @classmethod
    def _email_lower(cls, v: str | None) -> str | None:
        return _lower(v)

    @field_validator("member_since")
    @classmethod
    def _since_not_future(cls, v: date | None) -> date | None:
        return _not_future(v)


class MemberOut(BaseModel):
    id: int
    name: str
    email: str
    member_since: date
    open_loans: int
