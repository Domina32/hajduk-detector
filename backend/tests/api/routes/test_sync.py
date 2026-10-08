from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


@pytest.fixture(scope="module")
def per_file_setup() -> Generator[None]:
    """Once per file: above yield = setup, below = teardown."""
    yield


@pytest.fixture
def per_test_setup() -> Generator[None]:
    """Per test (default scope): same yield pattern."""
    yield


DERBY = {
    "idEvent": "2482560",
    "strTimestamp": "2026-10-10T13:00:00",
    "strHomeTeam": "Hajduk Split",
    "strAwayTeam": "Dinamo Zagreb",
    "strLeague": "Croatian First Football League",
    "strVenue": "Gradski stadion Poljud",
    "idVenue": "18136",
    "strStatus": "NS",
}

PAYLOAD = {"events": [DERBY]}


def test_create_sync_run(
    client: TestClient, superuser_token_headers: dict[str, str], monkeypatch
) -> None:
    monkeypatch.setattr("app.services.sportsdb.fetch_round", lambda **kwargs: PAYLOAD)
    monkeypatch.setattr(
        "app.services.sportsdb.fetch_team_events", lambda **kwargs: {"events": []}
    )

    response = client.post(
        f"{settings.API_V1_STR}/games/sync", headers=superuser_token_headers, json={}
    )
    assert response.status_code == 200
    content = response.json()
    assert content["created"] == 1
    assert content["error"] is None
    assert content["rounds"] == [9, 10, 11]


def test_create_sync_run_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {}
    response = client.post(
        f"{settings.API_V1_STR}/games/sync",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "The user doesn't have enough privileges"


def test_get_sync_run_status(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.sportsdb.fetch_round", lambda **kwargs: PAYLOAD)
    monkeypatch.setattr(
        "app.services.sportsdb.fetch_team_events", lambda **kwargs: {"events": []}
    )

    response = client.post(
        f"{settings.API_V1_STR}/games/sync",
        headers=superuser_token_headers,
        json={"rounds": [10]},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["created"] == 1
    assert content["error"] is None
    assert content["rounds"] == [10]


def test_sync_failure_is_recorded(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    def _boom(*_args: object, **_kwargs: object) -> None:
        raise Exception("boom")

    monkeypatch.setattr("app.services.sportsdb.fetch_round", _boom)
    monkeypatch.setattr(
        "app.services.sportsdb.fetch_team_events", lambda **kwargs: {"events": []}
    )

    response = client.post(
        f"{settings.API_V1_STR}/games/sync",
        headers=superuser_token_headers,
        json={},
    )
    assert response.status_code == 500
    content = response.json()
    assert "boom" in content["detail"]

    response = client.get(
        f"{settings.API_V1_STR}/games/sync/status",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["error"] == "boom"
    assert content["finished_at"] is not None


def test_get_sync_run_status_no_sync_runs(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/games/sync/status",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "No sync has run yet"
