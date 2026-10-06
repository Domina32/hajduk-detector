import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import col, func, select

from app.api.deps import (
    SessionDep,
    get_current_active_superuser,
    get_current_user,
)
from app.models import Game, GameCreate, GamePublic, GamesPublic, GameUpdate, Message

router = APIRouter(
    prefix="/games",
    tags=["games"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=GamesPublic)
def read_games(
    session: SessionDep,
    from_: datetime | None = Query(default=None, alias="from"),
    to_: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=500),
) -> Any:
    """
    Retrieve games.
    """

    if from_ is not None and from_.tzinfo is None:
        from_ = from_.replace(tzinfo=UTC)
    if to_ is not None and to_.tzinfo is None:
        to_ = to_.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    lower = from_ if from_ is not None else now
    filters = [Game.kickoff >= lower]
    if to_ is not None:
        filters.append(Game.kickoff <= to_)

    count = session.exec(select(func.count()).select_from(Game).where(*filters)).one()

    games = session.exec(
        select(Game).where(*filters).order_by(col(Game.kickoff).asc()).limit(limit)
    ).all()

    games_public = [GamePublic.model_validate(game) for game in games]
    return GamesPublic(data=games_public, count=count)


@router.get("/{id}", response_model=GamePublic)
def read_game(session: SessionDep, id: uuid.UUID) -> Any:
    """
    Get game by ID.
    """
    game = session.get(Game, id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=GamePublic
)
def create_game(*, session: SessionDep, game_in: GameCreate) -> Any:
    """
    Create new game.
    """
    game = Game.model_validate(game_in)
    session.add(game)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Game with this external_id already exists"
        )
    session.refresh(game)
    return game


@router.patch(
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=GamePublic,
)
def update_game(
    *,
    session: SessionDep,
    game_in: GameUpdate,
    id: uuid.UUID,
) -> Any:
    """
    Update a game.
    """
    game = session.get(Game, id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    update_dict = game_in.model_dump(exclude_unset=True)
    game.sqlmodel_update(update_dict)
    session.add(game)
    session.commit()
    session.refresh(game)
    return game


@router.delete("/{id}", dependencies=[Depends(get_current_active_superuser)])
def delete_game(session: SessionDep, id: uuid.UUID) -> Message:
    """
    Delete a game.
    """
    game = session.get(Game, id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    session.delete(game)
    session.commit()
    return Message(message="Game deleted successfully")
