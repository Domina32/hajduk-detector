# Docker Compose Deployment

The step-by-step procedure for running the app on a private server with
outgoing traffic only. The model and the reasoning are in
[deployment.md](./deployment.md).

## Preparation

- A server (a box on your home network is fine) with
  [Docker](https://docs.docker.com/engine/install/) installed (Docker Engine,
  not Docker Desktop).
- Nothing else. No domain, no DNS, no reverse proxy, no TLS certificate —
  nothing connects to this app from outside.

## Copy the Code

```bash
rsync -av --exclude=".git/" --filter=":- .gitignore" ./ user@your-server:/srv/hajduk/
```

The `--filter=":- .gitignore"` option tells `rsync` to use the same ignore
rules as Git, excluding files such as the Python virtual environment and
`.env`.

## Configure the Application

Create the environment file on the server from the template:

```bash
cd /srv/hajduk/
cp .env.example .env
chmod 600 .env
```

Then fill it in. The required values are:

```env
PROJECT_NAME="Poljud Games"
SECRET_KEY=<openssl rand -hex 32>
FIRST_SUPERUSER=you@example.com
FIRST_SUPERUSER_PASSWORD=<a real password>
POSTGRES_PASSWORD=<openssl rand -hex 32>
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/app
```

**Set all three secrets to real values.** The app refuses to start while
`SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD` or `POSTGRES_PASSWORD` is still
`changethis` — there is no development mode that relaxes this, so a
placeholder can never reach a running deployment.

Plus whatever the feature set needs:

```env
THESPORTSDB_API_KEY=123
SMTP_HOST=smtp.example.com
SMTP_USER=<user>
SMTP_PASSWORD=<password>
EMAILS_FROM_EMAIL=you@example.com
```

And, once M3 lands, the Sheets API grant:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
```

`DATABASE_URL` points at the `db` service, not `localhost` — the backend runs
in a container and reaches Postgres over the Docker network.

Check the file before deploying:

```bash
just check-env
```

## Deploy

```bash
cd /srv/hajduk/
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

Listing both files explicitly excludes the local development override
(`compose.override.yml`), which would otherwise publish ports.

`compose.deploy.yml` only adds `restart: always` to the long-running services.
There is no proxy and no port publishing: the stack is reachable only from
inside the Docker network on the host.

## Verify

```bash
docker compose -f compose.yml -f compose.deploy.yml ps
docker compose -f compose.yml -f compose.deploy.yml logs -f backend
```

The backend's health check is `/api/v1/utils/health-check/`. From the host:

```bash
docker compose -f compose.yml -f compose.deploy.yml exec backend \
  curl -f http://localhost:8000/api/v1/utils/health-check/
```

## Verify nothing is exposed

```bash
docker compose -f compose.yml -f compose.deploy.yml ps --format '{{.Service}}\t{{.Ports}}'
```

The `Ports` column must be empty for `backend` and `db`. If it is not, you are
running with the development override — use the explicit `-f` flags above.

For a belt-and-braces check on the host:

```bash
ss -tlnp | grep -E ':(8000|5432|80|443)\b' || echo "nothing exposed"
```

## Updating

```bash
git pull
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

## Backups

Postgres holds the fixture history, which the Sheet can be rebuilt from, but
the `Notification` table is not recoverable — it records which reminders were
already sent. If losing that matters, snapshot the volume:

```bash
docker compose -f compose.yml -f compose.deploy.yml exec -T db \
  pg_dump -U postgres app > "hajduk-$(date +%F).sql"
```
