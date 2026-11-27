Provide a reproducible isolated local preview for the frontend candidate and real backend, PostgreSQL and MinIO. Use a separate Compose project; do not touch existing production services. Loopback-only browser access; users can tunnel the printed URL. Worker/training is not required for the initial UI/data-preparation preview and must not be falsely claimed running. Preserve volumes on stop. No hardcoded production credentials or Git-tracked generated secrets. This is not a production deployment.

## Current correction — plain SQL schema initialization
Use `backend/sql/schema.sql` as the single canonical, repeatable schema initializer. It must preserve every SQL statement from the previously delivered initial schema revision and remain idempotent and non-destructive for fresh databases and existing legacy databases. Compose uses a one-shot `postgres:15-alpine` service running `psql -v ON_ERROR_STOP=1 -1 -f /schema/schema.sql` after PostgreSQL is healthy and before API/worker start. API, worker, and seed never apply DDL. Keep the old `alembic_version` table and its data untouched when present. Demo seeding remains an explicit separate command. No Alembic dependency, config, migrations, versions, or Python SQL execution wrapper remains in the current implementation. Preserve existing preview data and never silently drop user data.

## Historical proposal — backend-owned Alembic migrations (superseded)
The previous implementation assigned all schema definitions to `backend/migrations` with Alembic revision tracking. It used a one-shot backend-image migration before API/worker, with separate explicit demo seeding. This proposal was superseded by the plain SQL initializer correction above; its verification record remains historical evidence, not current implementation guidance.

Hosted preview correction: build and run this non-production candidate on the
current 2.56.97.211 server through Dokploy Compose. Existing production edge
terminates public HTTPS and forwards to the dedicated authenticated gateway over
TLS with pinned CA and SNI. Do not install conflicting ingress on the current
host or modify unrelated Caddy services. All passwords stay canonical; hostname
and environment-specific overrides remain declarative. A created resource is
not deployment proof.

## Historical hosted-gateway auth proposal — superseded

The earlier candidate retained HTTP Basic at the gateway but bridged browser
JWTs using the public `apiTokenHeader` (hosted override
`X-MGTS-Authorization`) and rewrote that header to backend `Authorization`.
This was superseded by the current browser HTTP Basic contract in
[`primevue-sakai-admin-workspace`](../primevue-sakai-admin-workspace/specs/admin-workspace/spec.md):
the gateway forwards the original `Authorization` header unchanged, the
frontend has no custom login/token-cookie bridge, and SSR forwards the incoming
header only to its configured internal API target. The old behavior remains
historical evidence, not current implementation guidance. Gateway protection
and the absence of public bypasses/default credentials remain required.
