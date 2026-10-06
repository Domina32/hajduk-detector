import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import Game, GameCreate
from tests.utils.game import create_game_at, create_random_game


@pytest.fixture(scope="module")
def per_file_setup() -> Generator[None]:
    """Once per file: above yield = setup, below = teardown."""
    yield


@pytest.fixture
def per_test_setup() -> Generator[None]:
    """Per test (default scope): same yield pattern."""
    yield


def test_create_game(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "home_team": "Home Team",
        "away_team": "Away Team",
        "competition": "Competition",
        "kickoff": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/games/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["home_team"] == data["home_team"]
    assert content["away_team"] == data["away_team"]
    assert content["competition"] == data["competition"]
    assert datetime.fromisoformat(content["kickoff"]) == datetime.fromisoformat(
        data["kickoff"]
    )
    assert "id" in content
    assert content["source"] == "manual"
    assert content["locked"] is False


def test_create_game_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {
        "home_team": "Home Team",
        "away_team": "Away Team",
        "competition": "Competition",
        "kickoff": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
    }
    response = client.post(
        f"{settings.API_V1_STR}/games/", headers=normal_user_token_headers, json=data
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "The user doesn't have enough privileges"


def test_create_game_duplicate_external_id(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "home_team": "Home Team",
        "away_team": "Away Team",
        "competition": "Competition",
        "kickoff": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "external_id": "nonunique",
    }
    first_response = client.post(
        f"{settings.API_V1_STR}/games/", headers=superuser_token_headers, json=data
    )
    second_response = client.post(
        f"{settings.API_V1_STR}/games/", headers=superuser_token_headers, json=data
    )
    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"] == "Game with this external_id already exists"
    )


def test_read_game(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    game = create_random_game(db)
    response = client.get(
        f"{settings.API_V1_STR}/games/{game.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(game.id)
    assert datetime.fromisoformat(response.json()["kickoff"]) == game.kickoff


def test_read_game_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/games/{uuid.uuid4()}", headers=normal_user_token_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_read_games(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/games/", headers=normal_user_token_headers
    )
    content = response.json()
    assert content["count"] == len(content["data"])
    kickoffs = [game["kickoff"] for game in content["data"]]
    assert kickoffs == sorted(kickoffs)


def test_read_games_from_to(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    now = datetime.now(UTC)
    early = create_game_at(db, now + timedelta(days=5))  # before  from  -> excluded
    middle = create_game_at(db, now + timedelta(days=20))  # inside window -> included
    late = create_game_at(db, now + timedelta(days=40))  # after   to    -> excluded

    response = client.get(
        f"{settings.API_V1_STR}/games/",
        headers=normal_user_token_headers,
        params={
            "from": (now + timedelta(days=10)).replace(tzinfo=None).isoformat(),
            "to": (now + timedelta(days=25)).replace(tzinfo=None).isoformat(),
        },
    )
    assert response.status_code == 200
    ids = {game["id"] for game in response.json()["data"]}
    assert str(middle.id) in ids
    assert str(early.id) not in ids
    assert str(late.id) not in ids


def test_read_games_no_auth(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/games/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_game(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    game = create_random_game(db)
    response = client.patch(
        f"{settings.API_V1_STR}/games/{game.id}",
        headers=superuser_token_headers,
        json={"venue_name": "New venue name"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["home_team"] == game.home_team
    assert content["away_team"] == game.away_team
    assert content["competition"] == game.competition
    assert datetime.fromisoformat(content["kickoff"]) == game.kickoff
    assert content["venue_name"] == "New venue name"


def test_update_game_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.patch(
        f"{settings.API_V1_STR}/games/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"home_team": "new home team"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_update_game_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    game = create_random_game(db)
    response = client.patch(
        f"{settings.API_V1_STR}/games/{game.id}",
        headers=normal_user_token_headers,
        json={"home_team": "new home team"},
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "The user doesn't have enough privileges"


def test_delete_game(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    game = create_random_game(db)
    response = client.delete(
        f"{settings.API_V1_STR}/games/{game.id}", headers=superuser_token_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Game deleted successfully"


def test_delete_game_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/games/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_delete_game_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    game = create_random_game(db)
    response = client.delete(
        f"{settings.API_V1_STR}/games/{game.id}", headers=normal_user_token_headers
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "The user doesn't have enough privileges"
