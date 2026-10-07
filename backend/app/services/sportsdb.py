from datetime import UTC, datetime
from typing import Any

import httpx
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Game, GameCreate, GameSource, GameStatus

SPORTSDB_TEAM_ID = "134019"
SPORTSDB_VENUE_ID = "18136"
SPORTSDB_LEAGUE_ID = "4629"

STATUS_MAP = {
    "NS": GameStatus.scheduled,
    "FT": GameStatus.finished,
    "PST": GameStatus.postponed,
    "CANC": GameStatus.cancelled,
}

SEASON = "2026-2027"
ROUND_NO = 9


def fetch_round(league_id: str, round_no: int, season: str) -> dict[str, Any]:
    response = httpx.get(
        f"https://www.thesportsdb.com/api/v1/json/{settings.THESPORTSDB_API_KEY}/eventsround.php",
        params={"id": league_id, "r": round_no, "s": season},
        timeout=20,
    )
    response.raise_for_status()
    return dict(response.json())


def fetch_team_events(team_id: str) -> dict[str, Any]:
    response = httpx.get(
        f"https://www.thesportsdb.com/api/v1/json/{settings.THESPORTSDB_API_KEY}/eventsnext.php",
        params={
            "id": team_id,
        },
    )
    response.raise_for_status()
    return dict(response.json())


def parse_events(payload: dict[str, Any]) -> list[GameCreate]:
    games = []
    events = [
        event
        for event in payload.get("events") or []
        if str(event.get("idVenue")) == "18136"
    ]
    for event in events:
        kickoff = datetime.fromisoformat(event["strTimestamp"]).replace(tzinfo=UTC)
        games.append(
            GameCreate(
                external_id=str(event["idEvent"]),
                home_team=event["strHomeTeam"],
                away_team=event["strAwayTeam"],
                competition=event["strLeague"],
                kickoff=kickoff,
                venue_name=event["strVenue"],
                venue_id=str(event["idVenue"]),
                status=STATUS_MAP.get(
                    event.get("strStatus") or "NS", GameStatus.scheduled
                ),
                source=GameSource.api,
            )
        )
    return games


def sync_events(
    session: Session, *, round_numbers: list[int], team_ids: tuple[str, ...]
) -> dict[str, int]:
    seen: dict[str, GameCreate] = {}

    for round_no in round_numbers:
        for game_in in parse_events(
            fetch_round(league_id=SPORTSDB_LEAGUE_ID, round_no=round_no, season=SEASON)
        ):
            if game_in.external_id is None:
                continue
            seen[game_in.external_id] = game_in

    for team_id in team_ids:
        for game_in in parse_events(fetch_team_events(team_id=team_id)):
            if game_in.external_id is None:
                continue
            seen.setdefault(game_in.external_id, game_in)

    created = updated = 0
    for game_in in seen.values():
        game = session.exec(
            select(Game).where(Game.external_id == game_in.external_id)
        ).first()
        if game is None:
            session.add(Game.model_validate(game_in))
            created += 1
        elif not game.locked:
            game.sqlmodel_update(game_in.model_dump(exclude={"external_id", "source"}))
            session.add(game)
            updated += 1

    session.commit()
    return {"created": created, "updated": updated}
