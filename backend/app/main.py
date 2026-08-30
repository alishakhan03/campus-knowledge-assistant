import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import app.db.base FIRST, before any route imports touch the models
# indirectly - this registers every model on Base.metadata up front and
# avoids a circular-import error (app/models/user.py <-> app/db/base.py)
# that otherwise only surfaces when something imports a model module
# directly (e.g. seed.py) instead of going through db.base first.
from app.db import base  # noqa: F401
from app.api.routes import auth, chat, documents, users
from app.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("campus_assistant")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered RAG chatbot that answers student questions from official college documents.",
    version="1.0.0",
)


def _allowed_origins() -> list[str]:
    """
    Build the CORS allow-list from FRONTEND_URL, including both the
    'localhost' and '127.0.0.1' forms of the same origin - browsers treat
    these as different origins even though they resolve to the same
    machine, and dev tooling (Vite, etc.) isn't always consistent about
    which one it reports/binds to.
    """
    origins = {settings.FRONTEND_URL}
    if "127.0.0.1" in settings.FRONTEND_URL:
        origins.add(settings.FRONTEND_URL.replace("127.0.0.1", "localhost"))
    elif "localhost" in settings.FRONTEND_URL:
        origins.add(settings.FRONTEND_URL.replace("localhost", "127.0.0.1"))
    return list(origins)


# CORS: only the configured frontend origin(s) are allowed - never "*" with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(users.router)


@app.on_event("startup")
def on_startup():
    logger.info("%s starting up in %s mode", settings.APP_NAME, settings.ENVIRONMENT)


@app.get("/api/health", tags=["system"], summary="Basic liveness check")
def health():
    return {"status": "ok"}


@app.get("/api/health/ready", tags=["system"], summary="Readiness check (DB + Pinecone)")
def readiness():
    checks = {"database": _check_database(), "pinecone": _check_pinecone()}
    overall_ok = all(checks.values())
    status_code = 200 if overall_ok else 503
    return JSONResponse(status_code=status_code, content={"status": "ok" if overall_ok else "degraded", "checks": checks})


def _check_database() -> bool:
    from sqlalchemy import text

    from app.db.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database readiness check failed")
        return False


def _check_pinecone() -> bool:
    try:
        from app.services.vector_service import get_vector_service

        return get_vector_service().health_check()
    except Exception:
        logger.exception("Pinecone readiness check failed")
        return False
