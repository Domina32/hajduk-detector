# Development

## Local Development

For local development, run PostgreSQL and Mailpit with Docker Compose, and run
the FastAPI development server locally.

The `justfile` wraps the whole flow. From the project root:

```bash
just dev
```

That starts Postgres and Mailpit, runs the migrations, and starts the backend
with reload. Open:

- Backend API: <http://localhost:8000>
- Interactive API docs: <http://localhost:8000/docs>
- Mailpit (captured mail): <http://localhost:8025>

`just --list` shows every recipe.

### Manual setup

If you prefer to run the steps yourself, from the project root:

```bash
docker compose up -d db mailpit
cd backend
uv sync
uv run bash scripts/prestart.sh
uv run fastapi dev
```

## Full Stack with Docker Compose

To run the backend in Docker Compose as well:

```bash
just stack
```

Stop a locally running FastAPI server before starting the Compose backend,
because both use port `8000`.

**Note**: the first time you start the stack, it might take a minute for all
the services to be ready. To monitor it, use `docker compose logs`, or
`docker compose logs backend` for the backend service.

## Mailpit

[Mailpit](https://mailpit.axllent.org) captures emails sent during local
development instead of delivering them. The local backend connects to it at
`localhost:1025`, and the Compose backend connects to the `mailpit` service.
Captured emails are available at <http://localhost:8025>.

## Docker Compose Files and Environment Variables

- `compose.yml` — the configuration shared by the whole stack. Docker Compose
  loads it automatically. It publishes no ports; the app is never exposed.
- `compose.override.yml` — local development settings: loopback-only port
  bindings for Postgres and Mailpit, source syncing and reload for the
  backend. Docker Compose applies it automatically on top of `compose.yml`.
- `compose.deploy.yml` — the private-server overlay. It is used explicitly, so
  the local override is not applied:
  `docker compose -f compose.yml -f compose.deploy.yml up -d`.

Docker Compose reads `.env` for variable interpolation and passes each
container the settings it needs. After changing variables, restart the stack.

## The `.env` File

`.env` is the single source of configuration. It holds the real secrets and is
gitignored; `.env.example` is the tracked template.

Create it once:

```bash
cp .env.example .env
```

Then fill in:

```env
SECRET_KEY=changethis
FIRST_SUPERUSER_PASSWORD=changethis
POSTGRES_PASSWORD=changethis
```

Generate the secrets with `openssl rand -hex 32` and pick a real
`FIRST_SUPERUSER_PASSWORD`. `just check-env` fails fast while any of them is
still a placeholder. The app itself refuses to start on a placeholder secret —
there is no development mode that relaxes this, so a placeholder can never
reach a running deployment by accident. The test suite is the exception:
`tests/conftest.py` injects its own secrets, so `just test-backend` works
without touching your `.env`.

`POSTGRES_PASSWORD` guards your local development database. Docker Compose
interpolates it out of `.env`, so it has to live there. After changing it,
update the already-initialised container, otherwise Postgres keeps the
password it was created with:

```bash
docker exec hajduk-detector-db-1 psql -U postgres -c "ALTER USER postgres PASSWORD '$POSTGRES_PASSWORD';"
```

If you run the full containerised backend rather than the dev server, pass the
file so the backend container sees the real values too:

```bash
docker compose --env-file .env up -d
```

## Editing Games by Hand

The fixture provider (TheSportsDB) is sometimes wrong, so games have to be
correctable by hand. `backend/scripts/game_admin.py` is a thin client over the
API, wrapped in `just` recipes:

```bash
just game-show   <game-uuid>
just game-lock   <game-uuid>
just game-unlock <game-uuid>
just game-set    <game-uuid> "kickoff=2026-10-17T19:00:00+00:00 home_team='Hajduk Split'"
```

A **locked** game is skipped by the fixture sync, so a manual correction is
not overwritten on the next run. Locking does not stop you editing the game
by hand — only syncs. Editable fields: `home_team`, `away_team`,
`competition`, `kickoff`, `venue_name`, `venue_id`, `status`.

The script talks to a running backend on `http://localhost:8000`; override
with the `API_URL` environment variable.

## Checks

The project uses [prek](https://prek.j178.dev/), a modern alternative to
[pre-commit](https://pre-commit.com/), for code linting and formatting.

Install the Git hook so `prek` runs automatically before each commit:

```bash
just prek-install
```

Now whenever you commit, `prek` checks and formats the code you are about to
commit. If it modifies any files, add those files to Git again before
committing.

Run it manually on all files from the project root:

```bash
just check
```

That runs ruff, pyrefly (the type checker, strict preset), typos and zizmor.
The narrower recipes are `just lint` (ruff only) and `just typecheck`
(pyrefly only).

## Tests

```bash
just test-backend
```

The suite runs against a dedicated `app_test` database derived from
`DATABASE_URL` — never against your development `app` database. It is created
and migrated automatically, and wiped before *and* after the run, so test users
can never leak into the dev database.
