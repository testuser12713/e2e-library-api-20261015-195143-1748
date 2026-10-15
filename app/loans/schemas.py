from datetime import datetime

from pydantic import BaseModel


class LoanCreate(BaseModel):
    book_id: int
    member_id: int


class LoanOut(BaseModel):
    id: int
    book_id: int
    member_id: int
    loaned_at: datetime
    due_at: datetime
    returned_at: datetime | None = None

    model_config = {"from_attributes": True}


class OverdueLoanOut(LoanOut):
    days_overdue: int
