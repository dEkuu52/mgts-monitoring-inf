# Preview: one command

Requires Docker Engine + Compose v2+ (no local Node/Python installation needed).

```sh
./scripts/preview.sh up
./scripts/preview.sh seed   # optional synthetic demo records
./scripts/preview.sh status
./scripts/preview.sh logs
./scripts/preview.sh down
```

Open http://127.0.0.1:3300/. On a remote server forward port 3300 with SSH
(`ssh -L 3300:127.0.0.1:3300 user@server`). Only the frontend is exposed,
on loopback. Containers listen internally on all interfaces. Do not publicly
publish this unauthenticated development stack or use its fixed demo credentials
in production. PostgreSQL, MinIO, API and frontend are isolated under Compose
project `mgts-preview`; existing production containers are not changed.

`up` rebuilds the candidate and waits for health checks. `down` preserves database,
photos and uploads; it never removes volumes. For another isolated instance use
both `MGTS_PREVIEW_PROJECT=mgts-preview-2` and `MGTS_PREVIEW_PORT=3301` consistently.
Readiness means HTTP services are running, not trained-model quality.

The preview uses the real API, not mock data. The explicit `seed` command populates synthetic demo records; `admin` / `admin123` is a preview-only account for the API's existing login/JWT clients, not a frontend login. The local preview defaults to `AUTH_REQUIRED=false` and the browser app redirects `/admin` to `/admin/objects`. These records are not ML evaluation results. YOLO
worker is deliberately not started: model provisioning and ML workbench are
separate workflows in the ML Draft PR (`cv/data_pipeline/README.md`). Uploaded
objects will not receive automatic inference until a worker is configured.
No dataset download or training happens during startup.

## Historical preview verification (prior candidate; not current auth proof)

The current server preview is forwarded to the laptop at
http://127.0.0.1:13300/admin (dedicated `mgts-frontend-tunnel` session).
The earlier candidate's login API, six admin routes and five seeded objects
returned successful HTTP responses. This is historical evidence for the prior
candidate, not verification of current HTTP Basic behavior. Browser automation
crashed before interactions, so no click-through verification is claimed. The
production Nitro build is not verified; this preview used the existing Nuxt
development Docker entrypoint.

Schema ownership: `backend/sql/schema.sql`. Compose waits for the one-shot
`schema-init` psql service to succeed before API/worker. API, worker and seed do
not apply DDL. The initializer uses `ON_ERROR_STOP` and one transaction; it is
safe to repeat and does not touch a legacy `alembic_version` table.
