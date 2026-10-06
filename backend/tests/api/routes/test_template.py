"""
TEMPLATE: copy this file to start a new test module.

Delete the ``pytestmark`` line below in your copy, or every ``test_*`` in
that copy will be reported as SKIPPED forever.

SETUP AND TEARDOWN LIVE AT THREE SCOPES

1. Whole suite   tests/conftest.py, fixture with scope="session"
                 (fill-in slot already added there: ``suite_setup``)
2. This file     fixture with scope="module"   (slot below)
3. Single test   fixture with scope="function" (pytest's default)

Teardown is the code AFTER ``yield``, never a second function: keeping
both halves at one indentation level is what stops them drifting apart.
"""

import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Game
from tests.utils.game import create_random_game

pytestmark = pytest.mark.skip("template: copy this file, then delete this line")


@pytest.fixture(scope="module")
def per_file_setup() -> Generator[None]:
    """Once per file: above yield = setup, below = teardown."""
    yield


@pytest.fixture
def per_test_setup() -> Generator[None]:
    """Empty slot: runs before every test that requests it as a parameter."""
    yield


@pytest.fixture
def fresh_game(db: Session) -> Generator[Game]:
    """Working example of scope 3: one game in, one game gone."""
    game = create_random_game(db)
    yield game
    db.delete(game)
    db.commit()


def test_example_create_game(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    payload = {
        "home_team": "Hajduk",
        "away_team": "Rijeka",
        "competition": "HNL",
        "kickoff": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "status": "postponed",
        "locked": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/games/",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "postponed"
    assert datetime.fromisoformat(content["kickoff"]) == datetime.fromisoformat(
        payload["kickoff"]
    )


def test_example_read_game(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    fresh_game: Game,
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/games/{fresh_game.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert datetime.fromisoformat(content["kickoff"]) == fresh_game.kickoff
    assert content["home_team"] == fresh_game.home_team


def test_example_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/games/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"
