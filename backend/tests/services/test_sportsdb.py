from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.models import Game, GameSource, GameStatus
from app.services import sportsdb
from app.services.sportsdb import (
    STATUS_MAP,
    current_season,
    discover_current_round,
    parse_events,
    resolve_rounds,
    sync_events,
)
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


def test_current_season() -> None:
    assert current_season(datetime(2026, 10, 8, tzinfo=UTC)) == "2026-2027"
    assert current_season(datetime(2027, 2, 1, tzinfo=UTC)) == "2026-2027"
    assert current_season(datetime(2027, 8, 1, tzinfo=UTC)) == "2027-2028"
    assert current_season(datetime(2027, 7, 1, tzinfo=UTC)) == "2027-2028"
    assert current_season(datetime(2027, 6, 30, tzinfo=UTC)) == "2026-2027"
    default = current_season()
    assert default[4] == "-" and len(default) == 9


def test_discover_current_round(monkeypatch) -> None:
    monkeypatch.setattr(
        sportsdb, "fetch_next_league", lambda **kwargs: {"events": [{"intRound": "9"}]}
    )
    assert discover_current_round("4629") == 9

    monkeypatch.setattr(
        sportsdb, "fetch_next_league", lambda **kwargs: {"events": None}
    )
    assert discover_current_round("4629") == 1

    monkeypatch.setattr(sportsdb, "fetch_next_league", lambda **kwargs: {"events": []})
    assert discover_current_round("4629") == 1

    monkeypatch.setattr(sportsdb, "fetch_next_league", lambda **kwargs: {})
    assert discover_current_round("4629") == 1

    def _boom(**_kwargs):
        raise Exception("boom")

    monkeypatch.setattr(sportsdb, "fetch_next_league", _boom)
    assert discover_current_round("4629") == 1


def test_resolve_rounds_explicit_makes_no_requests(monkeypatch) -> None:
    def _boom(**_kwargs):
        raise Exception("must not fetch")

    monkeypatch.setattr(sportsdb, "fetch_next_league", _boom)
    monkeypatch.setattr(sportsdb, "fetch_round", _boom)
    assert resolve_rounds([10, 11]) == [10, 11]


def test_resolve_rounds_auto_stops_at_first_empty(monkeypatch) -> None:
    calls: list[int] = []
    payload = {"events": [sample_event]}

    def _fake_fetch_round(**kwargs):
        calls.append(kwargs["round_no"])
        return payload if kwargs["round_no"] == 9 else {"events": []}

    monkeypatch.setattr(
        sportsdb, "fetch_next_league", lambda **kwargs: {"events": [{"intRound": "9"}]}
    )
    monkeypatch.setattr(sportsdb, "fetch_round", _fake_fetch_round)
    assert resolve_rounds(None) == [9]
    assert calls == [9, 10]


def test_resolve_rounds_auto_falls_back_to_round_one(monkeypatch) -> None:
    calls: list[int] = []

    def _fake_fetch_round(**kwargs):
        calls.append(kwargs["round_no"])
        return {"events": []}

    def _boom(**_kwargs):
        raise Exception("boom")

    monkeypatch.setattr(sportsdb, "fetch_next_league", _boom)
    monkeypatch.setattr(sportsdb, "fetch_round", _fake_fetch_round)
    assert resolve_rounds(None) == []
    assert calls == [1]
