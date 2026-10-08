# PLAN — Poljud Stadium Schedule → Google Sheet

Upcoming football games at **Gradski stadion Poljud, Split, Croatia** are
detected by the backend and published to a **shared Google Sheet**, with email
reminders before each game.

> **Pivot (2026-10-07): the app frontend is removed.** There is no dashboard
> UI. The backend remains the system of record (Game model, fixture sync,
> API routes, email reminders); presentation is a Google Sheet written via a
> dedicated Gmail account with OAuth. All "dashboard page" items below are
> superseded by M3.

This file is the working document: decisions at the top, task checklist below.
Items are checked off as they are completed, so the file always reflects the
real state of the build.

---

## Key decisions

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| 1 | Data source | **TheSportsDB, free key `123`** (no account, no payment) — replaces API-Football, whose free tier covers only 2022–2024 (verified 2026-10-07, see resolved question below). **Round-scoped polling**: `eventsround.php?id=4629&r=<n>&s=<season>` (league-wide, untruncated — full 5-game rounds verified) from the **dynamically discovered current round through season end**, filtered by venue `idVenue=18136` (`Gradski stadion Poljud`), **plus** team-scoped `eventsnext.php?id=134019` (Hajduk Split) to catch cup/Europe home games, which live under other league ids. `eventsnextleague.php` is unusable for fixtures on the free tier (returns 1 event — truncation quirk) but that single event's `intRound` is enough to discover the current round. Season string derived from the date (HNL spans Jul–Jun). Free tier: 30 req/min, no daily cap — pace round fetches ~2s apart; ~30 requests/day for a full season sweep is fine. | Must cover the *current* HNL season with venue info per fixture. football-data.org free tier excludes Croatia entirely. |
| 2 | Fallback data source | **Manual admin entry** (superuser CRUD API), then a scrape of hajduk.hr / hnl.hr if TheSportsDB coverage is unusable | Plan B if the key/Tier doesn't pan out. Built as part of the normal CRUD flow, so it costs almost nothing extra. |
| 3 | Dev cross-check | ~~TheSportsDB free key `123`~~ — promoted to primary source (decision 1); cross-check role dropped | — |
| 4 | Scope of games | **Venue-filtered**: any game whose venue is Poljud | Covers Hajduk home games *and* national team / cup games at the same stadium. |
| 5 | Read access | **Shared data — all logged-in users see the same games** | Unlike template `items` (owner-scoped), the whole point is one unified place. Writes restricted to superusers. |
| 6 | Notifications | **Email + Google Sheet** | Email via existing SMTP + react-email (1m/2w/1w/72h/48h reminders). The Sheet is the always-visible fixture list. No push/realtime in v1. |
| 7 | Scheduler | **APScheduler in-process** with FastAPI | Single deployment, no extra worker service in compose. One daily run does fixture sync + reminder check. Revisit if we ever need multiple backend replicas. |
| 8 | Reminder policy | **1 month, 2 weeks, 1 week, 72h and 48h before kickoff**, deduplicated per user per game | Five touchpoints cover "save the date" down to "final call". Dedupe table prevents resends. |
| 9 | Timezone | Store UTC, display **Europe/Zagreb**. TheSportsDB `strTimestamp` is naive but verified UTC (2026-10-10T13:00:00 = 15:00 local, derby cross-checked 2026-10-07); parser attaches UTC, never local. | Kickoff times come back in UTC-ish form; users are in Croatia. |
| 10 | Docs | This file (`PLAN.md` at repo root) | Decisions + checklist in one place, committed with the code. README stays user-facing; template docs untouched unless run/deploy steps change. |
| 11 | API key account + storage | Dedicated account **`hajduk-detector@protonmail.com`** (Proton Mail — no phone verification) registered with API-Sports; key **value** lives in untracked `.env.local`, only an empty placeholder in tracked `.env`. `.env.local` also carries `SECRET_KEY` and `FIRST_SUPERUSER_PASSWORD`. `Settings` loads `../.env` then `../.env.local` (later wins, missing file skipped), and Playwright's `tests/config.ts` mirrors that. | `.env` is committed in this template — a real key in it would persist in git history. Separate account keeps credentials transferable and off the personal inbox. `POSTGRES_PASSWORD` is the deliberate exception: Docker Compose interpolates it out of `.env` and it only guards the local dev DB. Outside development the app refuses to start while a fallback is still `changethis`. |
| 12 | Git workflow | Trunk-based: `master` stays green (CI-gated); **one branch per milestone** (`feat/m1-games-model` … `feat/m5-polish`), merged + pushed only after that milestone's work and tests pass. Commit messages mirror checklist items; `PLAN.md` checkbox updates ride in the same commit as the work. | Solo project — a branch per milestone costs ~4 commands each and buys a known-good rollback point per milestone. PRs are optional, not required: CI runs on plain pushes too (see #13). All git commands are run by the user; the agent does not run git. |
| 13 | CI scope | **One workflow, tests only**: `.github/workflows/ci.yml` runs backend pytest on **every push and every pull request** (frontend Playwright job deleted in M3, decision 16). Nothing else — no issue/PR templates, no labelers, no project board, no deploy workflow. | Single collaborator with no issue tracker: the only question CI needs to answer is "is the code green?". Lint/formatting stays local — the `prek` hooks run on `git commit`, so CI doesn't duplicate them. Actions are SHA-pinned because the `zizmor` hook enforces it. |
| 14 | Package manager | **npm** (not bun). Root `package.json` keeps the `packages/*` workspace for `packages/react-email`; `package-lock.json` at the repo root is the single lockfile. (Historical note: the template's Dockerfiles once referenced a non-existent `bun.lock`; the Playwright version pins died with `frontend/`.) | npm is already what the lockfile and the email tooling use. |
| 15 | Template `items` removal | **Remove the Items feature end-to-end.** Done so far: the `GET /items/` list route and its test, plus the **frontend surface** (`routes/_layout/items.tsx`, sidebar link, `tests/items.spec.ts`). Remaining: data layer (backend routes, `Item*` schemas, `crud.create_item`, `tests/api/routes/test_items.py`, `tests/utils/item.py`, `delete(Item)` in `tests/conftest.py`), then an `alembic revision` that drops the `item` table. Frontend-component leftovers (`components/Items/`, `PendingItems/`) go away with the whole frontend (decision 16) — no need to copy their dialog patterns anymore. | Games replace items as the product, so the list endpoint has no consumer left. |
| 16 | Presentation layer | **No app UI. Games are published to a Google Sheet** written by the backend through the **Google Sheets API**, authenticated as a **dedicated Gmail account via OAuth** (stored refresh token, secrets in `.env.local`). The `frontend/` app, its Playwright suite, the frontend CI job, `scripts/generate-client.sh`, and the generated client are deleted. Email reminders (SMTP + `packages/react-email`) stay — that package is backend mail templates, not UI. | Maintaining a full React dashboard for a read-only fixture list is overkill; a shared Sheet is what the consumers already use. A dedicated Gmail account keeps the OAuth grant transferable and off personal inboxes (same reasoning as decision 11). |
| 17 | Deployment | **Private local server, outgoing traffic only.** The app is never publicly deployed: no inbound ports, no domain, no Traefik/proxy exposure. The only egress is the Google Sheets API write (decision 16) and SMTP email send. `compose.yml` service exposure (`proxy`, labels, mailpit/adminer ports) and `deployment.md` / `deployment-docker-compose.md` are trimmed to match — local `docker compose up` for Postgres (+ Mailpit for dev), backend as a local process or container without published ports. | No consumers ever hit this app directly — they read the Sheet and receive email. Every open inbound port is attack surface with zero benefit; outgoing-only also sidesteps dynamic-IP / NAT issues on a home server. |

### Open question (resolved 2026-10-07)

- ~~**API-Football free tier coverage of the *current* season**~~ — **Resolved:
  NOT covered.** `GET /fixtures?league=210&season=2026` returns
  `"Free plans do not have access to this season, try from 2022 to 2024."`
  (verified live, ~4/100 daily requests used). Decision: try **TheSportsDB**
  (free key, quirks documented in #3) for current-season data first; if its
  coverage is unusable, scrape hajduk.hr / hnl.hr; manual superuser entry
  (M2 CRUD) remains the zero-dev fallback.

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
- [x] Paste real `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `API_FOOTBALL_API_KEY` into `.env.local`, set a real `POSTGRES_PASSWORD` in `.env`, then reset Postgres + the local superuser to match (`development.md` → "Real Secrets and `.env.local`"). Port 5432 also bound to `127.0.0.1` (`compose.override.yml`), since a real password is only worth having if the socket isn't LAN-reachable
- [x] Push and confirm both CI jobs are green on `master` (decision 13) — run 37218213673, both jobs passed
- [x] Install the `prek` git hook (`uv run prek install -f`) and clear the first full `uv run prek run --all-files` sweep
- [x] Consolidated task runner `justfile` (`just dev`, `just test-backend`, …); fixed the background-PID recipes (`mkdir -p /tmp/opencode`, `exec` so `kill` hits the server)
- [x] Separate test database: pytest runs against `app_test` (derived from `DATABASE_URL` in `tests/conftest.py`, overridable via `TEST_DATABASE_URL`), self-created + migrated, wiped before *and* after the suite — test users can never leak into dev `app` again

### M1 — Game model + migration

- [x] Add `Game` model to `backend/app/models.py`: `id`, `external_id` (provider fixture id, nullable for manual entries, unique), `home_team`, `away_team`, `competition`, `kickoff` (UTC, `DateTime(timezone=True)`), `venue_name`, `venue_id` (external), `status` (`scheduled/postponed/cancelled/finished`), `source` (`api/manual`), `created_at`, `updated_at`
- [x] Add public schemas `GameCreate` / `GameUpdate` / `GamePublic` / `GamesPublic`
- [x] Generate Alembic migration (`uv run alembic revision --autogenerate -m "add games"`) and review the generated file
- [x] Apply migration (`uv run alembic upgrade head`), confirm table exists

> **M1 notes** (decisions worth keeping): `GameStatus` / `GameSource` are Python
> `str`-mixin enums → PostgreSQL native `ENUM` types (`gamestatus`,
> `gamesource`), so adding a value later needs an `ALTER TYPE` migration.
> `updated_at` uses `onupdate` (`sa_column_kwargs`) — application-side only,
> invisible to Alembic; verified with an in-memory SQLite round-trip test
> (`created_at` must not move, `updated_at` must). `locked` (sync must not
> overwrite) is schema-only until M4 enforces it in the sync loop.
> Autogenerate's `downgrade()` did not drop the two enum types; hand-added
> `sa.Enum(...).drop(checkfirst=True)` and verified with
> `downgrade -1` / `upgrade head`.

### M2 — API routes

- [x] Create `backend/app/api/routes/games.py`: `GET /games` (upcoming by default, `?from=&to=&limit=`), shared across all users
- [x] Superuser-only `POST /games`, `PATCH /games/{id}`, `DELETE /games/{id}` (manual entry / corrections)
- [x] Register router in `backend/app/api/main.py`
- [ ] `POST /games/sync` (superuser, manual trigger) + `GET /games/sync/status` (last sync time, counts, errors) — moves with M4 sync work
- [x] Backend tests mirroring `tests/api/routes/test_items.py` (shared reads for normal users, write denied for non-superusers) — `tests/api/routes/test_games.py` + `tests/utils/game.py`
- [x] Regenerate frontend client: `./scripts/generate-client.sh` (last regen before frontend removal; script deleted in M3)

### M3 — Google Sheets output + frontend removal (supersedes dashboard)

- [ ] Google Cloud project + OAuth consent (dedicated Gmail account); `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN` in `.env.local`, empty placeholders in `.env`, `Settings` fields
- [ ] `backend/app/services/sheets.py`: write upcoming games to the target Sheet (columns: date/time Europe/Zagreb, home, away, competition, status, source); upsert-by-`external_id` semantics mirroring the DB sync so reruns don't duplicate rows
- [ ] Wire Sheet export into the sync flow (M4): every fixture sync refreshes the Sheet; plus superuser `POST /games/export` manual trigger
- [ ] Remove template Items, data layer (decision 15): remaining backend routes (`POST/PUT/DELETE /items`), `Item*` schemas, `crud.create_item`, `tests/api/routes/test_items.py`, `tests/utils/item.py`, `delete(Item)` in `tests/conftest.py`, then an `alembic revision` that drops the `item` table
- [x] Delete `frontend/`, root workspace bits, `scripts/generate-client.sh`; drop the frontend job from `.github/workflows/ci.yml` and frontend references in `justfile`/`compose` files/docs
- [ ] Manual smoke test: `just db` → backend sync → verify rows in the Sheet

### M4 — Sync + notifications

- [x] **Verify TheSportsDB coverage of current-season HNL/Poljud fixtures** with the free key before writing the parser — full round 9 (5 games, all venues with stable ids) confirmed; `eventsnextleague` truncated to 1 event, round-scoped polling chosen instead
- [x] `backend/app/services/sportsdb.py`: poll current + next HNL rounds (`eventsround`, league `4629`, season `2026-2027`) plus Hajduk `eventsnext` (team `134019`) for cup/Europe games; keep `idVenue=18136`, upsert by `external_id` (= `idEvent`; insert new, update kickoff/status for known, skip `locked`). Tests in `backend/tests/services/test_sportsdb.py` (parse + monkeypatched sync, no network). Timestamps are UTC (decision 9).
- [x] `API_FOOTBALL_API_KEY` added to `Settings` + empty placeholder in `.env` (value lives in `.env.local`) — pulled forward into M0; **removed 2026-10-07** (free tier lacks current season, decision 1): setting, `.env` placeholder, `.env.local` value all deleted
- [ ] Timezone normalization: external kickoff → UTC on write; verify against a known fixture
- [ ] APScheduler wiring in `backend/app/main.py`: one daily job for fixture sync + reminder check (gate on a `SCHEDULER_ENABLED` setting, not `FASTAPI_ENV`)
- [ ] `Notification` table: `user_id`, `game_id`, `kind` (`1m`/`2w`/`1w`/`72h`/`48h`), `sent_at`, unique constraint — dedupe so a user gets each reminder once
- [ ] react-email template `packages/react-email/emails/game_reminder.tsx` (teams, kickoff local time, venue, link to the Sheet)
- [x] `POST /games/sync` (superuser, manual trigger, optional `rounds` body — omitted means auto-discover current round through season end) + `GET /games/sync/status` (latest `SyncRun` row, 404 when never synced) — routes in `games.py` above `/{id}`, `SyncRun` table + migration, route tests in `tests/api/routes/test_sync.py` (monkeypatched, no network)
- [ ] Reminder job: find games starting in ~1m, ~2w, ~1w, ~72h and ~48h, send to active users (skipping users who opted out, M5), record in `Notification`. Poljud kickoffs move: when sync changes a game's kickoff, delete its `Notification` rows so reminders re-arm with the corrected time.
- [ ] Test end-to-end with Mailpit (`http://localhost:8025`)

### M5 — Polish

- [ ] Seed script / example data for a quick demo without an API key
- [ ] Superuser-toggled reminder emails: `email_reminders: bool = True` on `User`, flippable via existing superuser `PATCH /users/{user_id}` (no self-service — there is no frontend); reminder job skips opted-out users. Needs column migration.
- [ ] Lint + tests green: `uv run prek run --all-files`, backend pytest, single (backend-only) CI job green on `master` after the merge (decision 13)
- [ ] README section: what the app does, required `.env` vars (`THESPORTSDB_*`, `GOOGLE_*`), Sheet setup, scheduler + outgoing-only deployment (decision 17)
- [ ] Trim `deployment.md` / `deployment-docker-compose.md`, `compose.yml` (`proxy` service, Traefik labels, published ports) and any firewall/port docs to the outgoing-only model (decision 17)

---

## Working notes

- Conventions: routes in `backend/app/api/routes/`, schemas live in
  `backend/app/models.py` (template pattern). No frontend: do not reference
  `frontend/src/`, the generated client, or Playwright — all deleted in M3.
  `packages/react-email/` stays (backend mail templates).
- Backend tests: pytest in `backend/tests/` against the `app_test` database
  (self-provisioned by `tests/conftest.py`; never touch dev `app`).
  `tests/test_db.py` guards the isolation.
- CI (`.github/workflows/ci.yml`) runs the backend pytest suite on every push
  and PR (frontend job deleted in M3). `FASTAPI_ENV=development` is exported
  job-wide because `backend/app/frontend/` is gitignored and FastAPI refuses
  to start without it.
- No scattered `TODO` comments in code — if something is unfinished, it belongs
  in the checklist above.
- Open questions for M3: new-vs-existing target Sheet/Drive folder; exact
  OAuth flow (one-time manual grant → stored refresh token is the default
  assumption); sharing permissions on the Sheet.
