# Hajduk Detector

Upcoming football games at **Gradski stadion Poljud, Split, Croatia** are
detected by the backend and published to a **shared Google Sheet**, with email
reminders sent before each kickoff.

There is no web UI. The backend is the system of record: it syncs fixtures,
stores them, writes them to the Sheet, and sends the reminders. People read
the Sheet and receive the emails.

## How it works

```
TheSportsDB ──(sync)──> Postgres ──(export)──> Google Sheet
                             │
                             └──(reminders)──> email
```

- **Fixture sync** — `services/sportsdb.py` polls the current HNL rounds from
  TheSportsDB plus Hajduk's own fixtures (for cup and European games), keeps
  only games at Poljud (`idVenue=18136`), and upserts them by `external_id`.
- **Database** — SQLModel models in `backend/app/models.py`: `Game`, `SyncRun`,
  `Notification`, `User`.
- **Sheet** — the scheduled games are written to a Google Sheet so the list is
  always visible without anyone touching the server.
- **Reminders** — five email touchpoints before kickoff (1 month, 2 weeks,
  1 week, 72 hours, 48 hours), deduplicated per user per game in the
  `Notification` table.

## Technology

- [FastAPI](https://fastapi.tiangolo.com) + [SQLModel](https://sqlmodel.tiangolo.com)
  + [Pydantic](https://docs.pydantic.dev) on [PostgreSQL](https://www.postgresql.org)
- [Alembic](https://alembic.sqlalchemy.org) for migrations
- [TheSportsDB](https://www.thesportsdb.com) (free key `123`) for fixtures
- [React Email](https://react.email) for the email templates
- [APScheduler](https://apscheduler.readthedocs.io) for the daily sync + reminder job
- [Google Sheets API](https://developers.google.com/sheets) for the Sheet
- [uv](https://docs.astral.sh/uv/) for Python packaging, [prek](https://prek.j178.dev/)
  for the git hooks, [pytest](https://pytest.org) for the tests

## Quick start

```bash
cp .env.example .env      # then fill in the secrets
just setup                # deps, git hooks, migrations, first superuser
just dev                  # backend on http://localhost:8000
```

`just setup` needs Docker (for Postgres and Mailpit) and `uv`.

The API is at <http://localhost:8000>, with interactive docs at
<http://localhost:8000/docs>. Mailpit captures outgoing mail at
<http://localhost:8025>.

## Everyday commands

Everything is driven by the `justfile`. `just --list` shows all recipes.

| Command | What it does |
|---|---|
| `just dev` | Postgres + Mailpit, then the backend with reload |
| `just stack` | The whole stack in Docker Compose |
| `just test-backend` | The pytest suite (own `app_test` database) |
| `just check` | All pre-commit hooks: ruff, pyrefly, typos, zizmor |
| `just lint` | ruff only, fast |
| `just typecheck` | pyrefly, strict preset |
| `just revision "message"` | Autogenerate an Alembic migration |
| `just game-show <id>` | Print one game |
| `just game-lock <id>` | Stop fixture syncs from overwriting a game |
| `just game-unlock <id>` | Let syncs update it again |
| `just game-set <id> "kickoff=..."` | Edit a game's fields by hand |
| `just db-down` / `just nuke` | Stop services / stop and delete the volume |

### Editing games by hand

The fixture provider is sometimes wrong, so games are human-editable. A
**locked** game is skipped by the sync, which keeps a manual correction from
being overwritten:

```bash
just game-lock   <game-uuid>
just game-set    <game-uuid> "kickoff=2026-10-17T19:00:00+00:00 home_team='Hajduk Split'"
just game-unlock <game-uuid>
```

## Configuration

All configuration lives in `.env` in the project root. It is **gitignored**;
`.env.example` is the tracked template.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs the access tokens. `openssl rand -hex 32` |
| `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` | The bootstrap superuser |
| `POSTGRES_PASSWORD` | Local database password. Read by Docker Compose |
| `DATABASE_URL` | Connection string. `POSTGRES_PASSWORD` is interpolated |
| `THESPORTSDB_API_KEY` | TheSportsDB key. The free key `123` works |
| `SMTP_*`, `EMAILS_FROM_EMAIL` | Outgoing mail |
| `GOOGLE_*` | Sheets API OAuth credentials (M3) |

The app refuses to start outside development while a secret is still
`changethis`. `just check-env` checks the same thing locally.

## Deployment

The app runs on a **private server with outgoing traffic only** — it is never
published to the internet. There are no inbound ports, no domain and no
reverse proxy. The only outbound traffic is the Sheets API write and SMTP.

See [deployment.md](./deployment.md) for the model and
[deployment-docker-compose.md](./deployment-docker-compose.md) for the
step-by-step procedure.

## Project layout

```
backend/            FastAPI app, tests, Alembic migrations
  app/api/routes/   HTTP routes (games, login, users)
  app/services/     sportsdb sync, reminders, sheets
  app/models.py     SQLModel tables and API schemas
  tests/            pytest suite
packages/react-email/  React Email templates (source of the sent HTML)
compose.yml         Shared Compose configuration
compose.override.yml  Local development overlay
compose.deploy.yml  Private-server overlay
PLAN.md             Decisions and the milestone checklist
```

## Development docs

- [development.md](./development.md) — local setup, the `just` recipes, hooks
- [backend/README.md](./backend/README.md) — backend specifics, migrations, tests

## License

MIT — see [LICENSE](./LICENSE).
