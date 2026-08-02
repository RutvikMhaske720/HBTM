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
from app.db.database import SessionLocal, init_db
from app.db.seed import prepare_library


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    init_db()
    with SessionLocal() as db:
        # Fits the embedder and rebuilds the vector index before anything is
        # served. Skipping this is what previously left the index holding
        # vectors from a space the running process could no longer reproduce.
        report = prepare_library(db)
    print(
        f"[IABTM] Library ready — {report['library_size']} items, "
        f"{report['reindexed']} indexed"
        + (f", {report['migrated']} migrated" if report["migrated"] else "")
        + (f", {report['pruned']} pruned" if report["pruned"] else "")
    )
    if not settings.youtube_configured:
        print("[IABTM] YOUTUBE_API_KEY is unset — Videos, Animation and YouTube music are unavailable.")
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

    @app.get("/", include_in_schema=False)
    def redirect_to_docs():
        return RedirectResponse(url="/docs")

    return app
    return app


app = create_app()
