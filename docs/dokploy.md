# Dokploy preview

Source: GitHub `DanielTitovsky/mgts-infrastructure-monitoring`, branch
`feat/primevue-sakai-ui`, compose path `compose.dokploy.yml`.

One configuration chain: local service defaults in `compose.preview.yml`,
hosted overrides in `compose.dokploy.yml`. The one-shot `schema-init` service
applies `backend/sql/schema.sql` before API startup. Demo seeding is explicit,
not part of schema initialization.
Frontend defaults remain editable in `frontend/config.ts`; environment overrides
are for deployment-specific values.

Build and run the preview on `2.56.97.211`; publish gateway HTTPS on 18443.
Route public HTTPS through Dokploy-managed production Traefik with a dedicated
file-provider route, pinned gateway root CA and matching SNI; never disable TLS verification. Database, object storage and API
have no published host ports (only the authenticated TLS gateway does). Caddy's
HTTP Basic authentication protects every gateway path and forwards the original
`Authorization` header without a custom-header rewrite. Browser requests use
same-origin `/api/*` paths and browser-managed Basic credentials; SSR forwards
the incoming `Authorization` only to the configured internal API target. With
hosted `AUTH_REQUIRED=true`, FastAPI validates Basic credentials through the
existing user database and continues to accept Bearer JWTs for existing API
clients. The frontend has no custom login form, token cookie, or fake logout
action and stores no credentials. Browser credential caching is user-agent
controlled: the application cannot reliably clear the Basic cache or guarantee
a 30-day browser session. This preserves gateway protection on every path
without a public API bypass or default admin seeding. Populate the required
`MGTS_*` variables from the canonical secret store; never commit their values.

Current operator identity: project `rghjtik2yNArKL1FfDyCX`, environment
`Em_m45h4dBvE_x57nvVrC`, compose `cYpwjyQRKQhuu5i5U53F_`.
Archive-backed hosted deployment is running. The exposed Dokploy Compose
schema supports a runtime server at creation but no separate build-server
selection; ignored update keys are not placement proof. Live API readback verifies
`serverId=tmFr-4nexNmvrBWB0ng4g`, resolving to `2.56.97.211`. Builds on this
host are intended and authorized; the build restriction applies to production
`159.195.51.237`, not this host. Private Git clone was unavailable; use the archive path below.

Stop/rollback through Dokploy; preserve volumes. Never replace another service
or remove data to repair a preview.

The initial empty null-server candidate `X8-i_K7MTW-1i7W9gZ7tZ` was never
deployed; it is not the active runtime target. Native Compose server placement
is creation-only. The supported current target explicitly selects
`tmFr-4nexNmvrBWB0ng4g` and builds there, not on the production edge.

## Hackathon source delivery without GitHub administrator access

The user selected an alternative to Deploy keys because neither available GitHub account has repository administration. The SSH clone failed with Repository not found. The current Dokploy source is therefore `raw`, not Git auto-clone.

The Compose model is derived from `docker compose -f compose.dokploy.yml config --no-interpolate --format json`; preserve secret placeholders and use the existing protected Dokploy environment. Strip generated project-level network/volume names so deployment data remains isolated. Build contexts point to `/etc/dokploy/compose/mgts-preview-current-fnnfi5/source-4065ab8/{backend,frontend}`. That directory was populated through the Dokploy server operator from `git archive 4065ab8c30199aec8b94944ab3950570cfeef749 backend frontend`. Dokploy performs the actual build and start, on the existing build/runtime host. No GitHub credential is embedded in a URL or image, and no runtime source bind mounts are used.

Direct worktree contexts failed because the Dokploy user cannot traverse the private home directory; do not relax home permissions. Use a revision-specific archive in the managed service directory. For the raw Compose model, project the canonical bcrypt hash into gateway environment with each `$` escaped as `$$`. In JavaScript use `split('$').join('$$')`, not a replacement string whose `$$` means one dollar. Never reuse sanitized MCP `get_compose.composeFile` as writable configuration: it contains `[redacted]`; regenerate from the repository. The normal Git source remains a future option if repository read access is provisioned. This is a temporary manual source-delivery workflow, not automatic CI. Trusted public HTTPS: https://mgts.159.195.51.237.sslip.io/admin. The original traefik.me hostname hit the shared certificate issuance limit; sslip.io is used publicly while upstream TLS keeps its pinned CA and original SNI. Gateway account is `admin`, application account is `admin`; passwords stay in the canonical secret store. Synthetic example records are not real inspection results. Historical JWT-cookie candidate evidence: the hosted JWT lifetime was set to 30 days, but browser-managed HTTP Basic credentials have no application-guaranteed duration.
