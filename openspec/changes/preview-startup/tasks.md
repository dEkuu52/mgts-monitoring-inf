# Isolated preview startup
- [x] Provide one-command isolated Compose preview with persistent data and no public DB/storage ports.
- [x] Provide up/status/logs/down; never remove data volumes automatically.
- [x] Run syntax/config checks and live health/API proxy verification.
- [x] Publish with the frontend Draft PR; keep ML workbench in its independent ML Draft.
- [x] Fix fresh database prerequisite: base tables must exist before API additive schema bootstrap; initialization must be non-destructive/idempotent.
- [x] Seed existing idempotent demo records; verify login API and populated table API.
- [x] Historical browser click smoke was attempted, but both installed Chrome and headless shell crashed before interaction; the latest explicit instruction supersedes click testing, so do not run browser tests or claim UI-click verification.
- [ ] Verify the candidate through HTTP/API, build, and SQL checks only; do not claim browser click behavior.

Evidence: Compose health ready; laptop forwarded /admin HTTP 200 at http://127.0.0.1:13300/admin; login API 200; six admin routes 200; objects API returns five synthetic records. Draft PR #1 published; production Nitro build remains incomplete. ML Draft #2 is independent.
- [x] Historical intermediate correction: remove duplicate scripts/preview-schema.sql; use root migrations.sql, later superseded by backend Alembic and then by the current plain SQL initializer below. Verify fresh schema and repeated application preserves existing records.

Historical intermediate correction (superseded by backend Alembic, then the current plain SQL initializer below): migrations.sql creates missing base tables without DROP; isolated PostgreSQL transaction proved fresh creation and repeat application preserves a sentinel record. Duplicate SQL removed.
- [x] Backend Alembic revisions and legacy/fresh parity tests; remove startup DDL and obsolete SQL owners.
- [x] Compose one-shot migration ordering for API/worker; update both launchers to explicit seed.
- [x] Historical Alembic verification: fresh, existing and repeat data preservation passed; see the evidence below. It is not current startup guidance.
- [x] Publish correction in PR1, verify remote/PR SHA and commits membership; redeploy without deleting volumes.
- [ ] Deploy separate MGTS preview through Dokploy from canonical PR branch; provision external HTTPS route and protect access; verify outside localhost. Do not replace unrelated services.
- [x] [HISTORICAL — superseded by `primevue-sakai-admin-workspace` browser HTTP Basic correction] Preserve gateway Basic authentication on every hosted path while forwarding browser JWTs through configurable `X-MGTS-Authorization`; restore backend `Authorization`, strip the transport header, and keep SSR on standard `Authorization`. Add focused frontend/Compose checks and validate Caddy syntax/order; do not add public bypasses or default admin credentials.

Historical Alembic verification (superseded): 6 semantic/source tests; offline DDL emission; live PostgreSQL fresh + legacy-base + repeated upgrade passed, sentinel user preserved. Old SQL parity was proven against commit 05a644f before removal. The populated local preview was restarted through scripts/preview.sh up: all five objects survived, `alembic_version` was 20261124_0001, backend/frontend healthy and /admin HTTP 200. At that time, external hosted routing and the migration-failure runtime gate remained pending. This record documents only the former implementation; it is not proof for the current SQL initializer.

- [x] Replace the current Alembic startup path with `backend/sql/schema.sql`, preserving the prior revision's SQL statements and legacy `alembic_version` data without touching it; use one-shot `postgres:15-alpine` psql initialization before API/worker.
- [x] Remove Alembic dependencies, config, migration sources and image copies; update compose variants, launchers, static tests and current docs.
- [x] Update the live SQL verification script for fresh, repeat, and legacy preservation cases; run static/config checks without containers.
- [x] Run the updated live SQL verification: fresh, repeat, legacy schema/data preservation all passed; three sentinel records and prior version row preserved.

- [x] Verify Dokploy Compose placement by exact serverId/IP: build and runtime on 2.56.97.211, never build on production 159.195.51.237.
- [x] Resolve false-positive compound-command push guard before publishing (merged PR373); no bypass.

- [x] Apply merged personal guard fix PR373 through canonical sync; frontend push and PR1 SHA/commits readback now pass at 4065ab8.
- [x] Honor user-selected hackathon source delivery without GitHub admin: render existing Compose, stage exact Git archive through Dokploy operator, build using managed revision-specific contexts; preserve auth and secrets.
- [x] [HISTORICAL — verifies the prior custom app-login/JWT bridge only] Verify archive-backed deployment 7122dea: HTTPS unauthenticated401/authenticated200, app login200, authenticated objects/statuses/users200; both logins admin.

- [x] Provision requested preview credentials from canonical secrets and synthetic admin/demo records (not default seed passwords).
- [x] Restore rendered Compose from repository after sanitized MCP readback was mistakenly reused; never submit redacted API output as configuration.
- [x] Correct bcrypt literal escaping with split/join (JavaScript replacement strings interpret `$$`); public gateway now accepts configured credentials.
- [x] [HISTORICAL — superseded by browser-managed Basic credential caching; not a 30-day browser-session guarantee] Verify deployed persistent-cookie source and 30-day JWT via HTTP; 19 frontend unit tests pass. Browser persistence is not runtime-tested per explicit prohibition.

Historical runtime evidence (2026-11-25, source 7122dea238230b3aeed0355d9300dc205c1f49c0): deployed through Dokploy with the prior JWT bridge; Alembic package/config/migrations absent in backend image. SQL initializer succeeded; existing demo data and admin preserved. Public URL and temporary access credentials were recorded in private PR1. This is not evidence for the current HTTP Basic candidate. No browser checks remain or were run after removal.
