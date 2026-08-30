import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.database import get_db
from app.main import app

# Tests run against an in-memory SQLite DB - fast, isolated, and requires no
# MySQL/Pinecone/Gemini credentials. Only unit-level backend logic is covered
# here; real Pinecone/Gemini calls belong in separate "integration" tests
# (not included) that would be marked and skipped by default.
# StaticPool is required for in-memory SQLite so every session/connection in
# a test shares the SAME in-memory database instead of each getting its own.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # BackgroundTasks (document processing) open their own session via
    # app.db.database.SessionLocal rather than the get_db dependency, since
    # the request-scoped session is closed by the time a background task
    # runs in production. Point that at the same in-memory test DB/session
    # so uploads triggered in tests don't try to hit a real MySQL server.
    monkeypatch.setattr("app.db.database.SessionLocal", lambda: db_session)
    monkeypatch.setattr("app.api.routes.documents.SessionLocal", lambda: db_session)

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
