from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app import crud
from app.models import Game, GameCreate
from tests.utils.utils import random_lower_string


def create_random_game(db: Session) -> Game:
    home_team = random_lower_string()
    away_team = random_lower_string()
    competition = random_lower_string()
    kickoff = (datetime.now(UTC) + timedelta(days=30)).isoformat()
    game_in = GameCreate(
        home_team=home_team,
        away_team=away_team,
        competition=competition,
        kickoff=kickoff,
    )
    return crud.create_game(session=db, game_in=game_in)


def create_game_at(
    db: Session, kickoff: datetime, home_team: str = "Home Team"
) -> Game:
    return crud.create_game(
        session=db,
        game_in=GameCreate(
            home_team=home_team,
            away_team="Away Team",
            competition="Competition",
            kickoff=kickoff,
        ),
    )
