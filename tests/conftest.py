import secrets
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.clock import get_now
from app.config import Settings
from app.db import init_db, make_engine
from app.main import create_app


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)

    def advance(self, delta: timedelta) -> None:
        self.now += delta

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        library_api_key=secrets.token_hex(16),
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
    )


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def client(settings: Settings, clock: Clock) -> Iterator[TestClient]:
    app = create_app(settings)
    app.dependency_overrides[get_now] = clock
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api_headers(settings: Settings) -> dict[str, str]:
    return {"X-API-Key": settings.library_api_key or ""}


@pytest.fixture
def session(settings: Settings, client: TestClient) -> Iterator[Session]:
    engine = make_engine(settings)
    init_db(engine)
    with Session(engine, expire_on_commit=False) as s:
        yield s
    engine.dispose()
