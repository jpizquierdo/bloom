"""Shared pytest fixtures.

API tests run against a disposable ``bloom_test`` database on the same Postgres
instance. The schema is built once from the ORM metadata; every test starts from
a clean slate (all tables truncated). The app's ``get_db`` dependency is
overridden to use the test session, and the lifespan (admin bootstrap) is
skipped by not entering the TestClient as a context manager.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Ensure the startup admin bootstrap is inert during tests.
os.environ.pop("BLOOM_ADMIN_EMAIL", None)
os.environ.pop("BLOOM_ADMIN_PASSWORD", None)

import bloom.db.models  # noqa: F401  (register all models on Base.metadata)
from bloom.core.config import get_settings
from bloom.core.dependencies import get_db
from bloom.db.base import Base
from bloom.main import create_app
from bloom.services import users_service

TEST_DB_NAME = "bloom_test"
_ALL_TABLES = '"user", bean, brew, tasting, brew_method, equipment'


def _test_database_url() -> str:
    base = str(get_settings().SQLALCHEMY_DATABASE_URI)
    return base.rsplit("/", 1)[0] + "/" + TEST_DB_NAME


@pytest.fixture(scope="session")
def engine():
    """Create the test database (if needed), build the schema, yield an engine."""
    admin_engine = create_engine(
        str(get_settings().SQLALCHEMY_DATABASE_URI), isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    admin_engine.dispose()

    engine = create_engine(_test_database_url())
    # Recreate the schema from the current models so the test DB never drifts
    # (create_all alone would not pick up columns added since a previous run).
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )


@pytest.fixture(autouse=True)
def _clean_tables(engine):
    """Truncate all tables before each test for isolation."""
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {_ALL_TABLES} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db(session_factory) -> Session:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory) -> TestClient:
    """A TestClient with get_db overridden to the test database."""
    app = create_app()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Note: not used as a context manager, so the lifespan/admin bootstrap is skipped.
    return TestClient(app)


@pytest.fixture
def users(db) -> dict:
    """Seed an admin and two standard users; return them by role/name."""
    return {
        "admin": users_service.create_user(
            db, email="admin@example.com", password="adminpass1", role="admin"
        ),
        "alice": users_service.create_user(
            db, email="alice@example.com", password="alicepass1", role="user"
        ),
        "bob": users_service.create_user(
            db, email="bob@example.com", password="bobpass123", role="user"
        ),
    }


def _token(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _headers(client: TestClient, email: str, password: str) -> dict:
    return {"Authorization": f"Bearer {_token(client, email, password)}"}


@pytest.fixture
def admin_headers(client, users) -> dict:
    return _headers(client, "admin@example.com", "adminpass1")


@pytest.fixture
def alice_headers(client, users) -> dict:
    return _headers(client, "alice@example.com", "alicepass1")


@pytest.fixture
def bob_headers(client, users) -> dict:
    return _headers(client, "bob@example.com", "bobpass123")


@pytest.fixture
def lookups(client, admin_headers) -> dict:
    """Seed a filter method, an espresso method, and a grinder; return their ids."""
    filter_method = client.post(
        "/brew-methods",
        headers=admin_headers,
        json={"name": "V60", "category": "filter", "default_ratio": "16.00"},
    ).json()
    espresso_method = client.post(
        "/brew-methods",
        headers=admin_headers,
        json={"name": "Espresso", "category": "espresso"},
    ).json()
    grinder = client.post(
        "/equipment",
        headers=admin_headers,
        json={"type": "grinder", "name": "Niche Zero"},
    ).json()
    return {"filter": filter_method, "espresso": espresso_method, "grinder": grinder}
