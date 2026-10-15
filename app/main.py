from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import health
from app.books.router import router as books_router
from app.config import Settings, get_settings
from app.db import init_db, make_engine
from app.errors import register_exception_handlers
from app.loans.inspection_router import router as inspection_router
from app.loans.lending_router import router as lending_router
from app.members.router import router as members_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_db(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Library lending API", version="1.0.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.settings = settings
    app.dependency_overrides[get_settings] = lambda: settings
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(books_router)
    app.include_router(members_router)
    # inspection first: /loans/overdue must win over /loans/{loan_id}
    app.include_router(inspection_router)
    app.include_router(lending_router)
    return app


app = create_app()
