import os
from collections.abc import Generator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

os.environ["DATABASE_URL"] = urlunsplit(
    urlsplit(
        {
            **dotenv_values(Path(__file__).resolve().parents[2] / ".env"),
            **dotenv_values(Path(__file__).resolve().parents[2] / ".env.local"),
        }["DATABASE_URL"]
    )._replace(path="/app_test")
)

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Game, Item, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

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
