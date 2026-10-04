# PLAN — Poljud Stadium Schedule Dashboard

One shared place where multiple people can check whether there is an upcoming
football game at **Gradski stadion Poljud, Split, Croatia**, with email
reminders before each game.

This file is the working document: decisions at the top, task checklist below.
Items are checked off as they are completed, so the file always reflects the
real state of the build.

---

## Key decisions

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| 1 | Data source | **API-Football free tier** (100 req/day, API key in `.env`) | Full HNL fixture list in ~1 call/day; every fixture carries a `venue` object we filter to Poljud. Verified no free alternative covers HNL: football-data.org free tier excludes Croatia entirely. |
| 2 | Fallback data source | **Manual admin entry** (CRUD on the dashboard) | Plan B if the API key runs out or the API changes. Built as part of the normal CRUD flow, so it costs almost nothing extra. |
| 3 | Dev cross-check | **TheSportsDB** free key `123` (no signup) | Used only while developing, to sanity-check that API-Football data is complete. Not called in production. Known quirks: truncated free results and inconsistent kickoff times. |
| 4 | Scope of games | **Venue-filtered**: any game whose venue is Poljud | Covers Hajduk home games *and* national team / cup games at the same stadium. |
| 5 | Read access | **Shared data — all logged-in users see the same games** | Unlike template `items` (owner-scoped), the whole point is one unified place. Writes restricted to superusers. |
| 6 | Notifications | **Email + dashboard** | Email via existing SMTP + react-email. Dashboard shows upcoming games + "next game" countdown. No push/realtime in v1. |
| 7 | Scheduler | **APScheduler in-process** with FastAPI | Single deployment, no extra worker service in compose. Reminder job hourly, fixture sync daily. Revisit if we ever need multiple backend replicas. |
| 8 | Reminder policy | **24h and 2h before kickoff**, deduplicated per user per game | Two touchpoints cover "plan the trip" and "leave now". Dedupe table prevents resends. |
| 9 | Timezone | Store UTC, display **Europe/Zagreb** | Kickoff times come back in UTC-ish form; users are in Croatia. |
| 10 | Docs | This file (`PLAN.md` at repo root) | Decisions + checklist in one place, committed with the code. README stays user-facing; template docs untouched unless run/deploy steps change. |
| 11 | API key account + storage | Dedicated account **`hajduk-detector@protonmail.com`** (Proton Mail — no phone verification) registered with API-Sports; key **value** lives in untracked `.env.local`, only an empty placeholder in tracked `.env`. `.env.local` also carries `SECRET_KEY` and `FIRST_SUPERUSER_PASSWORD`. `Settings` loads `../.env` then `../.env.local` (later wins, missing file skipped), and Playwright's `tests/config.ts` mirrors that. | `.env` is committed in this template — a real key in it would persist in git history. Separate account keeps credentials transferable and off the personal inbox. `POSTGRES_PASSWORD` is the deliberate exception: Docker Compose interpolates it out of `.env` and it only guards the local dev DB. Outside development the app refuses to start while a fallback is still `changethis`. |
| 12 | Git workflow | Trunk-based: `master` stays green (CI-gated); **one branch per milestone** (`feat/m1-games-model` … `feat/m5-polish`), merged + pushed only after that milestone's work and tests pass. Commit messages mirror checklist items; `PLAN.md` checkbox updates ride in the same commit as the work. | Solo project — branches cost ~4 commands each and buy a known-good rollback point per milestone. PRs are optional, not required: CI runs on plain pushes too (see #13). All git commands are run by the user; the agent does not run git. |
| 13 | CI scope | **One workflow, tests only**: `.github/workflows/ci.yml` runs backend pytest + frontend Playwright on **every push and every pull request**. Nothing else — no issue/PR templates, no labelers, no project board, no deploy workflow. | Single collaborator with no issue tracker: the only question CI needs to answer is "is the code green?". Lint/formatting stays local — the `prek` hooks run on `git commit`, so CI doesn't duplicate them. Actions are SHA-pinned because the `zizmor` hook enforces it. |
| 14 | Package manager | **npm** (not bun). Root `package.json` is a workspace; `package-lock.json` at the repo root is the single lockfile. `@playwright/test` is pinned to the **exact same version** in both the root and `frontend/package.json`, and must be bumped together with `frontend/Dockerfile.playwright`'s base image tag. | The template's Dockerfiles referenced `bun.lock`, which does not exist in this repo — `docker compose build` was broken from day one. npm is already what the lockfile, `development.md` and the `root` scripts use. |

### Open question (resolve during Milestone 4)

- **API-Football free tier coverage of the *current* season** — their docs say
  "covers recent seasons", which is ambiguous. First task of M4 is a live
  verification call with the real key. If current season is excluded, fall back
  to TheSportsDB (with its quirks documented above) or a scrape of
  hajduk.hr / hnl.hr.

---

## Milestones

### M0 — Tooling baseline

- [x] Convert the project from bun to npm: `backend/Dockerfile`, `frontend/Dockerfile.playwright` (both referenced a non-existent `bun.lock`), `frontend/package.json` test scripts, `playwright.config.ts` web server command, `scripts/generate-client.sh`, docs, `pyproject.toml` typos exclude
- [x] Pin `@playwright/test` to the same exact version in the root and `frontend/package.json` (two versions were installed; the browser cache matched neither)
- [x] `.gitignore`: stop ignoring `.github*` so workflows can be committed; ignore `.env.local` (decision 11)
- [x] Fix the `biome` pre-commit hook: it passed repo-root paths to a process running in `frontend/` (always failed), and `biome.json` now excludes vendored assets in `public/`
- [x] Wire `.env.local` into `Settings` (`env_file=("../.env", "../.env.local")`) and into `frontend/tests/config.ts`, and gitignore it
- [x] Replace placeholder identity in `.env`: `PROJECT_NAME`, `FIRST_SUPERUSER`, `EMAILS_FROM_EMAIL` → real values; add `API_FOOTBALL_API_KEY` to `Settings` with an empty placeholder
- [x] `.github/dependabot.yml`: weekly grouped bump of the SHA-pinned GitHub Actions
- [ ] Paste real `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `API_FOOTBALL_API_KEY` into `.env.local`, set a real `POSTGRES_PASSWORD` in `.env`, then reset Postgres + the local superuser to match (`development.md` → "Real Secrets and `.env.local`")
- [ ] Push and confirm both CI jobs are green on `master` (decision 13)

### M1 — Game model + migration

- [ ] Add `Game` model to `backend/app/models.py`: `id`, `external_id` (API-Football fixture id, nullable for manual entries, unique), `home_team`, `away_team`, `competition`, `kickoff` (UTC, `DateTime(timezone=True)`), `venue_name`, `venue_id` (external), `status` (`scheduled/postponed/cancelled/finished`), `source` (`api/manual`), `created_at`, `updated_at`
- [ ] Add public schemas `GameCreate` / `GameUpdate` / `GamePublic` / `GamesPublic`
- [ ] Generate Alembic migration (`uv run alembic revision --autogenerate -m "add games"`) and review the generated file
- [ ] Apply migration (`uv run alembic upgrade head`), confirm table exists

### M2 — API routes

- [ ] Create `backend/app/api/routes/games.py`: `GET /games` (upcoming by default, `?from=&to=&limit=`), shared across all users
- [ ] Superuser-only `POST /games`, `PATCH /games/{id}`, `DELETE /games/{id}` (manual entry / corrections)
- [ ] Register router in `backend/app/api/main.py`
- [ ] `POST /games/sync` (superuser, manual trigger) + `GET /games/sync/status` (last sync time, counts, errors)
- [ ] Backend tests mirroring `tests/api/routes/test_items.py` (shared reads for normal users, write denied for non-superusers)
- [ ] Regenerate frontend client: `./scripts/generate-client.sh`

### M3 — Dashboard page

- [ ] Replace placeholder `_layout/index.tsx` with the Poljud dashboard: next-game hero card with countdown, then upcoming-games list (date, time in Europe/Zagreb, opponents, competition, status)
- [ ] Superuser-only "Add game" dialog + row actions (edit/delete), reusing `components/Items/` dialog patterns
- [ ] Empty states: "no upcoming games" and "never synced" (with Sync button for admins)
- [ ] Sidebar/nav labels updated (Items → Games), page titles updated
- [ ] Manual smoke test: `docker compose up -d db mailpit` → `uv run fastapi dev` → `npm run dev`

### M4 — Sync + notifications

- [ ] **Verify API-Football free key against current-season HNL fixtures** (open question above) — decide keep/switch before writing the parser. Key is already in `.env.local` (decision 11); the call itself is the remaining work.
- [ ] `backend/app/services/football_api.py`: fetch HNL fixtures, filter venue to Poljud, upsert by `external_id` (insert new, update kickoff/status for known, mark missing as cancelled)
- [x] `API_FOOTBALL_API_KEY` added to `Settings` + empty placeholder in `.env` (value lives in `.env.local`) — pulled forward into M0
- [ ] Timezone normalization: external kickoff → UTC on write; verify against a known fixture
- [ ] APScheduler wiring in `backend/app/main.py`: daily fixture sync + hourly reminder check (skipped when `FASTAPI_ENV != development`… re-evaluate: should run in prod too, so gate on a `SCHEDULER_ENABLED` setting instead)
- [ ] `Notification` table: `user_id`, `game_id`, `kind` (`24h`/`2h`), `sent_at`, unique constraint — dedupe so a user gets each reminder once
- [ ] react-email template `packages/react-email/emails/game_reminder.tsx` (teams, kickoff local time, venue, link to dashboard)
- [ ] Reminder job: find games starting in ~24h and ~2h, send to active users, record in `Notification`
- [ ] Test end-to-end with Mailpit (`http://localhost:8025`)

### M5 — Polish

- [ ] Seed script / example data for a quick demo without an API key
- [ ] User-facing settings: opt out of reminder emails (default: on)
- [ ] Lint + tests green: `uv run prek run --all-files`, backend pytest, `npm test`
- [ ] CI still green on `master` after the merge (decision 13)
- [ ] README section: what the app does, required `.env` vars (`API_FOOTBALL_API_KEY`), how to run scheduler locally
- [ ] Update `deployment.md` / `deployment-docker-compose.md` only if env vars or run steps changed

---

## Working notes

- Conventions: routes in `backend/app/api/routes/`, schemas live in
  `backend/app/models.py` (template pattern), frontend routes are file-based
  under `frontend/src/routes/`, API client is generated — never hand-edit
  `frontend/src/client/`.
- Frontend tests: Playwright (`npm test`), backend: pytest in
  `backend/tests/`.
- CI (`.github/workflows/ci.yml`) runs both suites on every push and PR. It
  starts `db` + `mailpit` via compose, migrates with `scripts/prestart.sh`, then
  runs pytest (backend job) or `npm test` against a locally started uvicorn
  (frontend job). `FASTAPI_ENV=development` is exported job-wide because
  `backend/app/frontend/` is gitignored and FastAPI refuses to start without it.
- Two things must move together when upgrading: the `@playwright/test` pin
  (root + `frontend/package.json`) and the `mcr.microsoft.com/playwright`
  base-image tag in `frontend/Dockerfile.playwright`.
- No scattered `TODO` comments in code — if something is unfinished, it belongs
  in the checklist above.
