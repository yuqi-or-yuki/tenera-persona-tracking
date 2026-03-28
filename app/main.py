from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (SQLite dev mode)
    if settings.database_mode == "sqlite":
        await init_db()
    yield


app = FastAPI(
    title="Tenera Persona Tracking",
    description=(
        "Open-source persona tracking and cohort analytics engine. "
        "Track user personas, attach arbitrary entities, and build event timelines. "
        "Designed to integrate seamlessly with Tenera."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
