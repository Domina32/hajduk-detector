from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.models import NotificationKind
from app.services.reminders import get_due_games
from tests.utils.game import create_game_at


def test_get_due_game_found_at_48h(db: Session) -> None:
    game = create_game_at(db=db, kickoff=datetime.now(UTC) + timedelta(hours=48))
    due = get_due_games(db, now=datetime.now(UTC))
    assert len(due) == 1
    assert due[0][0].id == game.id
    assert due[0][1] == NotificationKind.h48


def test_no_due_game_far_future(db: Session) -> None:
    create_game_at(db=db, kickoff=datetime.now(UTC) + timedelta(days=10))
    due = get_due_games(db, now=datetime.now(UTC))
    assert due == []
