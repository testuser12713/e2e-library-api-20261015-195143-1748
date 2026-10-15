from datetime import date

from pydantic import BaseModel, EmailStr, Field


class MemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    member_since: date | None = None


class MemberUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    email: EmailStr | None = None
    member_since: date | None = None


class MemberOut(BaseModel):
    id: int
    name: str
    email: str
    member_since: date
    open_loans: int
