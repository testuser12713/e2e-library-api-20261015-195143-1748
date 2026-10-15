from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import DateTime, Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from app.config import Settings


class Base(DeclarativeBase):
    pass


class UtcDateTime(TypeDecorator[datetime]):
    """Stores naive UTC, returns timezone-aware UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(UTC)
        return value.replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


def make_engine(settings: Settings) -> Engine:
    url = settings.database_url
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url)


def init_db(engine: Engine) -> None:
    import app.models  # noqa: F401  (registers the tables on Base)

    Base.metadata.create_all(engine)


def get_session(request: Request) -> Iterator[Session]:
    """One Session per request, bound to the engine of the running app."""
    session = Session(request.app.state.engine, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
