from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cache import close_cache, connect_cache
from .config import settings
from .db import close, connect, db, ensure_indexes
from .events import start_listener
from .routers import admin, ai, alerts, auth, dashboard, incidents, ws
from .seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    await connect_cache()
    await ensure_indexes(db())
    await seed_database(db())
    start_listener()
    yield
    await close_cache()
    await close()


def create_app() -> FastAPI:
    app = FastAPI(title="MonkLens API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(incidents.router)
    app.include_router(alerts.router)
    app.include_router(dashboard.router)
    app.include_router(ai.router)
    app.include_router(admin.router)
    app.include_router(ws.router)

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app
