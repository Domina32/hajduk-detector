from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User

# Setup slots -- request one as a test parameter to use it. Every scope,
# with worked examples: tests/api/routes/test_template.py


@pytest.fixture(scope="module")
def per_file_setup() -> Generator[None]:
    """Once per file: above yield = setup, below = teardown."""
    yield


@pytest.fixture
def per_test_setup() -> Generator[None]:
    """Per test (default scope): same yield pattern."""
    yield


def test_create_user(client: TestClient, db: Session) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/private/users/",
        json={
            "email": "pollo@listo.com",
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    assert r.status_code == 200

    data = r.json()

    user = db.exec(select(User).where(User.id == data["id"])).first()

    assert user
    assert user.email == "pollo@listo.com"
    assert user.full_name == "Pollo Listo"
