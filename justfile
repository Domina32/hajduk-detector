# Consolidated task runner. `just` lists recipes; `just <recipe>` runs one.
# Local dev = Postgres + Mailpit in compose.
# Full stack in compose = `just stack` (uses compose.override.yml automatically).

set dotenv-load := true
# Load `.env` (the single env file, gitignored) into the recipe environment.
# Compose reads `.env` itself; `Settings` reads it itself via `env_file`.
set dotenv-path := ".env"

_default:
    @just --list --unsorted

# ── Setup ──────────────────────────────────────────────────────────────

# First-time setup: tooling, deps, git hooks, migrated DB.
# Copy .env.example to .env and fill in the secrets before running this.
setup: install prek-install migrate
    @echo "Setup done. Run 'just dev' to start both servers."

# Install Python (uv) + JS (npm) dependencies.
install:
    uv sync
    npm install

# Install prek git hooks (runs lint/format on commit).
prek-install:
    uv run prek install -f

# Fail fast if required secrets are still placeholders.
[group('setup')]
check-env:
    #!/usr/bin/env bash
    set -euo pipefail
    missing=0
    if [ ! -f .env ]; then echo "MISSING .env (copy .env.example to .env)"; missing=1; exit $missing; fi
    for var in SECRET_KEY FIRST_SUPERUSER_PASSWORD POSTGRES_PASSWORD; do
      if grep -q "^${var}=changethis$" .env || ! grep -q "^${var}=.\+" .env; then
        echo "MISSING or placeholder ${var} in .env (see development.md)"; missing=1
      fi
    done
    exit $missing

# ── Services ───────────────────────────────────────────────────────────

# Start Postgres + Mailpit (detached, waits for health).
db:
    docker compose up -d --wait db mailpit

# Stop Postgres + Mailpit, keep volumes.
db-down:
    docker compose stop db mailpit

# Follow logs for one service (default: backend). `just logs db`.
logs service="backend":
    docker compose logs -f {{ service }}

# Run migrations + seed superuser. Needs DB up.
migrate: db
    cd backend && uv run bash scripts/prestart.sh

# Backend dev server at :8000. Starts DB + migrates first.
run-backend: db migrate
    cd backend && uv run fastapi dev



# Dev server: backend in foreground (Ctrl-C stops it cleanly).
dev: db migrate
    cd backend && uv run fastapi dev


# Full containerised stack (backend served at :8000). Stop local :8000 first.
stack: db
    docker compose run --rm backend bash scripts/prestart.sh
    docker compose watch

stack-down:
    docker compose down --remove-orphans

# ── Codegen / DB ───────────────────────────────────────────────────────



# New autogenerate migration. `just revision "add games"`.
revision message="auto":
    cd backend && uv run alembic revision --autogenerate -m "{{ message }}"

upgrade:
    cd backend && uv run alembic upgrade head

downgrade:
    cd backend && uv run alembic downgrade -1

# ── Tests ──────────────────────────────────────────────────────────────

# Backend pytest with coverage (mirrors CI backend job).
# Uses its own `app_test` database (see backend/tests/conftest.py),
# so it only needs Postgres up — never migrates the dev `app` DB.
test-backend: db
    cd backend && uv run bash scripts/tests-start.sh "local"


# Everything: backend suites.
test: test-backend

# ── Games ──────────────────────────────────────────────────────────────

# Show a game: just game-show <game-uuid>
game-show id:
    cd backend && uv run python scripts/game_admin.py show {{id}}

# Lock a game so fixture syncs stop overwriting it: just game-lock <game-uuid>
game-lock id:
    cd backend && uv run python scripts/game_admin.py lock {{id}}

# Let fixture syncs update a game again: just game-unlock <game-uuid>
game-unlock id:
    cd backend && uv run python scripts/game_admin.py unlock {{id}}

# Edit game fields by hand:
#   just game-set <game-uuid> "kickoff=2026-10-17T19:00:00+00:00 home_team='Hajduk Split'"
game-set id *fields:
    cd backend && uv run python scripts/game_admin.py set {{id}} {{quote(fields)}}

# ── Lint / checks ──────────────────────────────────────────────────────

# All prek hooks (ruff, pyrefly, typos, zizmor).
check:
    uv run prek run --all-files

# Fast lint subset: ruff only. Full check is `just check` (prek).
lint:
    uv run ruff check backend
    uv run ruff format --check backend


# Backend type check (pyrefly, strict preset) as run by prek.
typecheck:
    uv run pyrefly check

# ── Cleanup ────────────────────────────────────────────────────────────

# Remove volumes + orphans (DESTROYS local DB data). Stops everything first.
nuke:
    docker compose down -v --remove-orphans

# Drop node_modules / venv artefacts (recreated by `just setup`).
clean:
    rm -rf  .venv backend/.venv
