"""Admin helper for games: lock/unlock and edit fields by hand.

The fixture provider (TheSportsDB) is sometimes wrong, so games have to be
correctable by hand. A locked game is skipped by the sync, which keeps manual
corrections from being overwritten on the next run.

Usage:
    uv run python scripts/game_admin.py show   <game-id>
    uv run python scripts/game_admin.py lock   <game-id>
    uv run python scripts/game_admin.py unlock <game-id>
    uv run python scripts/game_admin.py set    <game-id> field=value [field=value ...]

Editable fields: home_team, away_team, competition, kickoff, venue_name,
venue_id, status (scheduled|postponed|cancelled|finished).
"""

import argparse
import os
import shlex
import sys
from typing import Any

import httpx

from app.core.config import settings

API_URL = os.getenv("API_URL", "http://localhost:8000")
EDITABLE_FIELDS = (
    "home_team",
    "away_team",
    "competition",
    "kickoff",
    "venue_name",
    "venue_id",
    "status",
)
VALID_STATUSES = ("scheduled", "postponed", "cancelled", "finished")


def _token(client: httpx.Client) -> str:
    """Log in as the first superuser and return an access token."""
    response = client.post(
        f"{API_URL}{settings.API_V1_STR}/login/access-token",
        data={
            "username": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    )
    response.raise_for_status()
    return str(response.json()["access_token"])


def _patch(client: httpx.Client, game_id: str, payload: dict[str, Any]) -> dict:
    response = client.patch(
        f"{API_URL}{settings.API_V1_STR}/games/{game_id}",
        json=payload,
    )
    if response.status_code == 404:
        sys.exit(f"No game with id {game_id}")
    if response.status_code == 422:
        sys.exit(f"Invalid values: {response.json().get('detail')}")
    response.raise_for_status()
    return dict(response.json())


def _parse_fields(pairs: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for pair in shlex.split(pairs):
        if "=" not in pair:
            sys.exit(f"Expected field=value, got {pair!r}")
        key, _, value = pair.partition("=")
        key = key.strip()
        if key not in EDITABLE_FIELDS:
            sys.exit(
                f"Cannot edit {key!r}. Editable fields: {', '.join(EDITABLE_FIELDS)}"
            )
        if key == "status" and value not in VALID_STATUSES:
            sys.exit(f"status must be one of: {', '.join(VALID_STATUSES)}")
        payload[key] = value
    if not payload:
        sys.exit("Nothing to change. Pass at least one field=value pair.")
    return payload


def _show(game: dict) -> None:
    print(f"id          {game['id']}")
    print(f"kickoff     {game['kickoff']}")
    print(f"home        {game['home_team']}")
    print(f"away        {game['away_team']}")
    print(f"competition {game['competition']}")
    print(f"venue       {game['venue_name']} ({game['venue_id']})")
    print(f"status      {game['status']}")
    print(f"source      {game['source']}")
    print(f"external_id {game['external_id']}")
    print(f"locked      {game['locked']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("show", "lock", "unlock", "set"), help="what to do"
    )
    parser.add_argument("game_id", help="the game's UUID")
    parser.add_argument(
        "fields", nargs="?", default="", help="field=value pairs (only for 'set')"
    )
    args = parser.parse_args()

    try:
        with httpx.Client(timeout=15) as client:
            token = _token(client)
            client.headers["Authorization"] = f"Bearer {token}"

            if args.command == "show":
                response = client.get(
                    f"{API_URL}{settings.API_V1_STR}/games/{args.game_id}"
                )
                if response.status_code == 404:
                    sys.exit(f"No game with id {args.game_id}")
                response.raise_for_status()
                _show(dict(response.json()))
                return

            if args.command == "lock":
                game = _patch(client, args.game_id, {"locked": True})
                print(f"Locked {game['id']}. Fixture syncs will not touch it.")
                return

            if args.command == "unlock":
                game = _patch(client, args.game_id, {"locked": False})
                print(f"Unlocked {game['id']}. Fixture syncs may update it again.")
                return

            game = _patch(client, args.game_id, _parse_fields(args.fields))
            print(f"Updated {game['id']}:")
            _show(game)
    except httpx.ConnectError:
        sys.exit(
            f"Cannot reach the API at {API_URL}. Is the backend running? "
            "Start it with 'just dev'."
        )


if __name__ == "__main__":
    main()
