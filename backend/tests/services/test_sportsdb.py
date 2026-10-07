from datetime import UTC

from sqlmodel import Session, select

from app.models import Game, GameSource, GameStatus
from app.services import sportsdb
from app.services.sportsdb import STATUS_MAP, parse_events, sync_events

sample_event = {
    "idEvent": "2482560",
    "idAPIfootball": "1548538",
    "strTimestamp": "2026-10-10T13:00:00",
    "strEvent": "Hajduk Split vs Dinamo Zagreb",
    "strEventAlternate": "Dinamo Zagreb @ Hajduk Split",
    "strFilename": "Croatian First Football League 2026-10-10 Hajduk Split vs Dinamo Zagreb",
    "strSport": "Soccer",
    "idLeague": "4629",
    "strLeague": "Croatian First Football League",
    "strLeagueBadge": "https://r2.thesportsdb.com/images/media/league/badge/bgo85e1781975278.png",
    "strSeason": "2026-2027",
    "strDescriptionEN": None,
    "strHomeTeam": "Hajduk Split",
    "strAwayTeam": "Dinamo Zagreb",
    "intHomeScore": None,
    "intHomeScoreExtra": None,
    "intAwayScoreExtra": None,
    "intRound": "9",
    "intAwayScore": None,
    "intSpectators": None,
    "strOfficial": "",
    "strWeather": None,
    "dateEvent": "2026-10-10",
    "dateEventLocal": None,
    "strTime": "13:00:00",
    "strTimeLocal": None,
    "strGroup": None,
    "idHomeTeam": "134019",
    "strHomeTeamBadge": "https://r2.thesportsdb.com/images/media/team/badge/23mvtk1579955412.png",
    "idAwayTeam": "133961",
    "strAwayTeamBadge": "https://r2.thesportsdb.com/images/media/team/badge/zcb6f61784988620.png",
    "intScore": None,
    "intScoreVotes": None,
    "strResult": None,
    "idVenue": "18136",
    "strVenue": "Gradski stadion Poljud",
    "strCountry": "Croatia",
    "strCity": None,
    "strPoster": "",
    "strSquare": "",
    "strFanart": None,
    "strThumb": "https://r2.thesportsdb.com/images/media/event/thumb/fcm9hz1780905669.jpg",
    "strBanner": "",
    "strMap": None,
    "strTweet1": None,
    "strVideo": None,
    "strStatus": "NS",
    "strPostponed": "no",
    "strLocked": "unlocked",
}

sample_event_away_postponed = {
    "idEvent": "2482564",
    "idAPIfootball": "1548537",
    "strTimestamp": "2026-10-09T16:00:00",
    "strEvent": "HNK Gorica vs Rudeš",
    "strEventAlternate": "Rudeš @ HNK Gorica",
    "strFilename": "Croatian First Football League 2026-10-09 HNK Gorica vs Rudeš",
    "strSport": "Soccer",
    "idLeague": "4629",
    "strLeague": "Croatian First Football League",
    "strLeagueBadge": "https://r2.thesportsdb.com/images/media/league/badge/bgo85e1781975278.png",
    "strSeason": "2026-2027",
    "strDescriptionEN": None,
    "strHomeTeam": "HNK Gorica",
    "strAwayTeam": "Rudeš",
    "intHomeScore": None,
    "intHomeScoreExtra": None,
    "intAwayScoreExtra": None,
    "intRound": "9",
    "intAwayScore": None,
    "intSpectators": None,
    "strOfficial": "",
    "strWeather": None,
    "dateEvent": "2026-10-09",
    "dateEventLocal": None,
    "strTime": "16:00:00",
    "strTimeLocal": None,
    "strGroup": None,
    "idHomeTeam": "137794",
    "strHomeTeamBadge": "https://r2.thesportsdb.com/images/media/team/badge/v77ket1579955421.png",
    "idAwayTeam": "141086",
    "strAwayTeamBadge": "https://r2.thesportsdb.com/images/media/team/badge/gykp4z1615834182.png",
    "intScore": None,
    "intScoreVotes": None,
    "strResult": None,
    "idVenue": "18467",
    "strVenue": "Gradski stadion Velika Gorica",
    "strCountry": "Croatia",
    "strCity": None,
    "strPoster": "",
    "strSquare": "",
    "strFanart": None,
    "strThumb": "https://r2.thesportsdb.com/images/media/event/thumb/hlsb4e1780905674.jpg",
    "strBanner": "",
    "strMap": None,
    "strTweet1": None,
    "strVideo": None,
    "strStatus": "PST",
    "strPostponed": "no",
    "strLocked": "unlocked",
}


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
