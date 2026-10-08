from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models import Game, GameStatus, NotificationKind

REMINDER_DELTAS: dict[NotificationKind, timedelta] = {
    NotificationKind.m1: timedelta(days=30),
    NotificationKind.w2: timedelta(weeks=2),
    NotificationKind.w1: timedelta(weeks=1),
    NotificationKind.h72: timedelta(hours=72),
    NotificationKind.h48: timedelta(hours=48),
}

TOLERANCE = timedelta(hours=12)


def get_due_games(
    session: Session, *, now: datetime
) -> list[tuple[Game, NotificationKind]]:
    """
    Games whose kickoff is ~delta away for each reminder tier.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    due: list[tuple[Game, NotificationKind]] = []
    games = session.exec(select(Game).where(Game.status == GameStatus.scheduled)).all()
    for game in games:
        kickoff = game.kickoff
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)
        for kind, delta in REMINDER_DELTAS.items():
            target = kickoff - delta
            if abs((target - now).total_seconds()) <= TOLERANCE.total_seconds():
                due.append((game, kind))
    return due
