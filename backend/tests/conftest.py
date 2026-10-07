import os
from collections.abc import Generator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlmodel import Session, delete


def _test_database_url() -> str:
    # Explicit override always wins (CI, custom local setup).
    if os.getenv("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]
    base = os.getenv("DATABASE_URL")
    if not base:
        env = {
            **dotenv_values(Path(__file__).resolve().parents[2] / ".env"),
            **dotenv_values(Path(__file__).resolve().parents[2] / ".env.local"),
        }
        base = env["DATABASE_URL"]

    if base.startswith("postgresql://postgres:${POSTGRES_PASSWORD}"):
        base = base.replace(
            "${POSTGRES_PASSWORD}", os.getenv("POSTGRES_PASSWORD", ""), 1
        )
    parts = urlsplit(base)
    if not (parts.path and parts.path != "/"):
        raise RuntimeError(f"Cannot derive test DB name from {base!r}")
    name = parts.path.lstrip("/")
    if not name.endswith("_test"):
        name = f"{name}_test"
    return urlunsplit(parts._replace(path=f"/{name}"))


os.environ["DATABASE_URL"] = _test_database_url()

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.db import engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Game, Item, User  # noqa: E402
from tests.utils.user import authentication_token_from_email  # noqa: E402
from tests.utils.utils import get_superuser_token_headers  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


def _create_db() -> None:
    live = urlsplit(str(settings.DATABASE_URL))
    admin = create_engine(
        urlunsplit(live._replace(path="/postgres")), isolation_level="AUTOCOMMIT"
    )
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": live.path[1:]}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{live.path[1:]}"'))
    admin.dispose()


def _migrate() -> None:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "app" / "alembic"))
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    _create_db()
    _migrate()
    with Session(engine) as session:
        for model in (Game, Item, User):
            session.execute(delete(model))
        session.commit()
        init_db(session)
        yield session

        for model in (Game, Item, User):
            session.execute(delete(model))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
