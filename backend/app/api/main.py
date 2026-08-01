"""FastAPI application factory.

Lifespan:
  - Creates all DB tables (idempotent via create_all).
  - Seeds the content library if empty.
  - CORS configured to allow the Next.js dev server.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.db.seed import seed_content_library
from app.db.database import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    init_db()
    with SessionLocal() as db:
        seeded = seed_content_library(db)
        if seeded:
            print(f"[IABTM] Seeded {seeded} content items.")
    print("[IABTM] Backend ready.")
    yield
    # Shutdown — nothing to clean up for SQLite


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="IABTM Agentic AI Curator",
        description="Backend API for the I Am Better Than Me platform.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.api.routers.users import router as users_router
    from app.api.routers.recommendations import router as recs_router
    from app.api.routers.agent import router as agent_router
    from app.api.routers.goals import router as goals_router
    from app.api.routers.identity import router as identity_router
    from app.api.routers.content import router as content_router

    app.include_router(users_router)
    app.include_router(recs_router)
    app.include_router(agent_router)
    app.include_router(goals_router)
    app.include_router(identity_router)
    app.include_router(content_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "IABTM Backend"}

    return app


app = create_app()
