from typing import Any

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class PageParams:
    def __init__(
        self,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> None:
        self.limit = limit
        self.offset = offset


def paginate(session: Session, select_stmt: Select, params: PageParams) -> tuple[list[Any], int]:
    """Run `select_stmt` for one page; returns (rows, total of all matches)."""
    count_stmt = select(func.count()).select_from(select_stmt.order_by(None).subquery())
    total = session.scalar(count_stmt) or 0
    rows = list(session.scalars(select_stmt.limit(params.limit).offset(params.offset)))
    return rows, total
