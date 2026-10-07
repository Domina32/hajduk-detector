from datetime import UTC
from zoneinfo import ZoneInfo

from sqlmodel import Session, delete, select

from app.models import Game, GameSource, GameStatus
from app.services import sportsdb
from app.services.sportsdb import STATUS_MAP, parse_events, sync_events
from tests.utils.sync_run import sample_event, sample_event_away_postponed


def test_parse_events() -> None:
    result = parse_events(
        payload={"events": [sample_event, sample_event_away_postponed]}
    )
    assert len(result) == 1
    assert result[0].home_team == "Hajduk Split"
    assert result[0].external_id == "2482560"
    assert result[0].kickoff.tzinfo == UTC
    assert result[0].status == GameStatus.scheduled
    assert result[0].source == GameSource.api
    assert STATUS_MAP["PST"] is GameStatus.postponed

    assert parse_events({"events": None}) == []


def test_sync_upserts_by_external_id(db: Session, monkeypatch) -> None:
    db.exec(delete(Game))
    db.commit()
    payload = {"events": [sample_event, sample_event_away_postponed]}
    monkeypatch.setattr(sportsdb, "fetch_round", lambda **kwargs: payload)
    monkeypatch.setattr(sportsdb, "fetch_team_events", lambda **kwargs: {"events": []})
    assert sync_events(db, round_numbers=[9], team_ids=()) == {
        "created": 1,
        "updated": 0,
    }
    assert sync_events(db, round_numbers=[9], team_ids=()) == {
        "created": 0,
        "updated": 1,
    }
    games = db.exec(select(Game)).all()
    assert len(games) == 1
    assert games[0].source == GameSource.api
    assert games[0].locked is False
    assert games[0].kickoff.tzinfo is not None
    assert games[0].kickoff.isoformat() == "2026-10-10T13:00:00+00:00"


def test_kickoff_stored_as_utc() -> None:
    result = parse_events(payload={"events": [sample_event]})
    kickoff = result[0].kickoff
    assert kickoff.tzinfo == UTC
    assert kickoff.isoformat() == "2026-10-10T13:00:00+00:00"
    local = kickoff.astimezone(ZoneInfo("Europe/Zagreb"))
    assert (local.hour, local.minute) == (15, 0)
