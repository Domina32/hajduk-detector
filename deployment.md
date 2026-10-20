# Deployment

The app runs on a **private server with outgoing traffic only**. It is never
published to the internet.

## The model

Nobody connects to this app. The consumers are:

- a **Google Sheet**, which people read;
- **email**, which people receive.

So the server needs no inbound connectivity at all:

- **No published ports.** Postgres and the backend stay on the Docker
  network. Nothing binds to `0.0.0.0` on the host.
- **No domain, no DNS, no reverse proxy, no TLS.** There is no HTTP surface
  to secure, because there is no HTTP surface.
- **No firewall exceptions.** The host's inbound policy can stay closed.
- **Egress only:** the Google Sheets API and your SMTP provider.

This also sidesteps dynamic-IP and NAT problems — a box on a home network
behind a router needs nothing exposed.

```
                 ┌──────────────────────────────┐
  internet ──────│  private server              │
  (no inbound)   │                              │
                 │   backend ──> Google Sheets  │
                 │      │                       │
                 │      └──────> SMTP provider  │
                 │                              │
                 │   postgres (docker network)  │
                 └──────────────────────────────┘
```

## What runs where

| Component | Where | Notes |
|---|---|---|
| `backend` | Docker container | FastAPI + the daily sync/reminder job |
| `postgres` | Docker container | Only reachable on the Docker network |
| Mailpit | **not deployed** | Development only. Production uses a real SMTP provider |

## Secrets

The container needs these at runtime, and they must not live in the image:

- `SECRET_KEY` — signs access tokens
- `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` — the bootstrap superuser
- `POSTGRES_PASSWORD` — the database password
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAILS_FROM_EMAIL` — outgoing mail
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` — the
  Sheets API grant (once M3 lands)

The Compose configuration reads them from the environment or from an `--env-file`.
Generate the random ones with:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Keep the file that holds them out of the repository, and out of the image
(`.dockerignore` already excludes `.env`).

### Secrets must be real

There is no environment-mode switch. The app **refuses to start** while
`SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD` or the `DATABASE_URL` password is
still `changethis` — in every environment, development included. That is the
point: a placeholder secret can never reach a running deployment by accident.

The test suite is the one exception, and it handles it itself:
`tests/conftest.py` injects its own `SECRET_KEY` and
`FIRST_SUPERUSER_PASSWORD` before the app is imported, so the tests never
depend on the real ones and CI needs to generate nothing.

## Procedure

The step-by-step commands are in
[deployment-docker-compose.md](./deployment-docker-compose.md).

## Verifying a deployment

The backend exposes a health check at `/api/v1/utils/health-check/`. From the
server itself:

```bash
docker compose -f compose.yml -f compose.deploy.yml exec backend \
  curl -f http://localhost:8000/api/v1/utils/health-check/
```

And check the logs for the scheduler doing its work:

```bash
docker compose -f compose.yml -f compose.deploy.yml logs -f backend
```

## Updates

Pull the new code, rebuild and restart:

```bash
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

`scripts/prestart.sh` runs the Alembic migrations and creates the first
superuser, so run it before `up -d` after any model change.
