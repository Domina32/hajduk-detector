# Consolidated task runner. `just` lists recipes; `just <recipe>` runs one.
# Local dev = Postgres + Mailpit in compose.
# Full stack in compose = `just stack` (uses compose.override.yml automatically).

set dotenv-load := true
# Load `.env.local` (real secrets) instead of `.env` (placeholders): exported
# vars beat Settings' own file lookup, so exporting `.env` would shadow the
# real values with "changethis". Compose reads `.env` itself; Settings reads
# both files itself; nothing in these recipes needs `.env` exported.
set dotenv-path := ".env.local"

_default:
    @just --list --unsorted

# ── Setup ──────────────────────────────────────────────────────────────

# First-time setup: tooling, deps, env files, git hooks, migrated DB.
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
    for f in .env .env.local; do
      [ -f "$f" ] || { echo "MISSING $f"; missing=1; }
    done
    if grep -q '^SECRET_KEY=$' .env.local 2>/dev/null || ! grep -q '^SECRET_KEY=.\+' .env.local 2>/dev/null; then echo "MISSING SECRET_KEY in .env.local (see development.md)"; missing=1; fi
    if grep -q '^FIRST_SUPERUSER_PASSWORD=$' .env.local 2>/dev/null || ! grep -q '^FIRST_SUPERUSER_PASSWORD=.\+' .env.local 2>/dev/null; then echo "MISSING FIRST_SUPERUSER_PASSWORD in .env.local"; missing=1; fi
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
    cd backend && FASTAPI_ENV=development uv run bash scripts/tests-start.sh "local"


# Everything: backend suites.
test: test-backend

# ── Lint / checks ──────────────────────────────────────────────────────

# All prek hooks (ruff, mypy, ty, biome, typos, client freshness).
check:
    uv run prek run --all-files

# Fast subset without regenerating the client: ruff + biome + typos.
lint:
    uv run ruff check backend/app
    uv run ruff format --check backend/app


# Backend type checks (mypy strict + ty) as run by prek.
typecheck:
    uv run mypy backend/app
    uv run ty check backend/app

# ── Cleanup ────────────────────────────────────────────────────────────

# Remove volumes + orphans (DESTROYS local DB data). Stops everything first.
nuke:
    docker compose down -v --remove-orphans

# Drop node_modules / venv artefacts (recreated by `just setup`).
clean:
    rm -rf  .venv backend/.venv
