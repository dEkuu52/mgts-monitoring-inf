## Frontend candidate

- [x] Review the existing PrimeVue/Sakai frontend changes against this change's requirements; keep the separately scoped preview infrastructure as an adjacent, documented candidate slice.
- [x] Complete review of the workspace, table, form, and object-photo implementation without replacing the current workflows.
- [x] Verify real API remains the default and demo mode is opt-in, visibly synthetic, and mock-backed.
- [x] Run focused frontend tests and update frontend instructions for the supported demo mode.
- [x] Complete a production build (verified after memory recovery; historical failure follows). The client and SSR bundles compiled, but the host `earlyoom` daemon sent SIGTERM to the Nitro Node process during generation when available memory fell below its 12% threshold with swap full; the earlyoom journal confirms the victim, and no Nuxt/Nitro error or successful build result is claimed. Retry only when host memory is safe.
- [x] Inspect the final frontend/OpenSpec diff and create one focused candidate commit.
- [x] Restore developer-owned frontend/config.ts defaults and connect them to Nuxt runtime config; environment overrides must still work.
- [x] [HISTORICAL — superseded by the browser HTTP Basic correction below] Persist the JWT cookie through browser restarts until its actual expiry (capped at 30 days), with cookie-option regression tests.
- [x] Remove browser automation checks per explicit user correction; do not run browser tests. Verify session expiry with unit tests and HTTP/API checks instead.

## Actual Sakai template adoption (in progress)
- [x] Import pinned upstream layout, styling, theme utilities and license; adapt Nuxt routing/state safely.
- [x] Apply upstream page/login/form/table patterns to all MGTS screens without changing API/photo contracts.
- [x] Remove superseded handcrafted shell/style artifacts after functionality mapping.
- [x] Verify upstream provenance, configuration/default API mode and focused regression tests.
- [ ] Build and run candidate with bounded resources; verify HTTP/API responses. Browser click verification is explicitly excluded by the user.
- [ ] Update existing Draft PR1 and Dokploy preview when publication is possible; do not claim a public URL without runtime proof.

Template integration evidence: npm ci passed; 16 Node tests passed; 15 page/table Vue SFCs compiled in the page slice. Coordinator compared all 19 imported asset files byte-for-byte against the pinned git submodule and verified the seven original layout/composable hashes. Fixed two integration regressions with red/green tests: explicitly import the nested Sakai composable in shell/topbar, and remove unused empty legacy site layout with unresolved CSS import. No custom legacy shell SCSS remains.

Build remains incomplete: first real build found and fixed legacy site import; next bounded 256MiB-heap build failed with explicit V8 heap exhaustion (exit 134). A larger build is currently unsafe under confirmed host earlyoom pressure (2.1GiB available with 1.9GiB threshold and full swap). Only this task's isolated frontend/backend/MinIO were temporarily stopped to reduce pressure and then restored; no unrelated services or memory protection were changed. Restored container images predate this template candidate; their health does not verify the new template. No new push/deploy attempted while the previously recorded push block remains unresolved; Hookify changes are expressly out of scope.

## Memory-recovery verification

- [x] Retry the exact Sakai candidate ecc56918b9b5be143cbe16f63592c8c91781e3a6 after host capacity recovered: `NODE_OPTIONS=--max-old-space-size=1536 npm run build` completed with exit 0, including Nitro. Canonical waiter run: `mgts-sakai-build-recovered-foreground`.
- [x] [HISTORICAL — evidence of the superseded custom-login/JWT-cookie implementation only; not a current auth contract or request to rerun] Run the built `.output/server/index.mjs` and DOM-only Playwright smoke against the real isolated preview API: login, all five navigation destinations and logout/cookie clearing passed. The skill `with_server.py` managed temporary candidate port 3301 and loopback API relay 3001 to the existing preview API on 3300; both test processes stopped afterward. No mocks, screenshots or published-runtime claims.
- [x] Extend and pass DOM-only form/photo smoke: open create form, fill type, reject non-image file, select synthetic PNG, verify blob preview, remove unsaved photo. No screenshot, image interpretation, upload persistence or ML processing claim. PrimeVue duplicates alt on its wrapper; use the actual img role for a strict locator.

The earlier memory-blocked notes above are historical and superseded by this successful build and navigation proof. Hosted publication remains pending; Dokploy readback still reports no deployments.

Latest correction: prior completed DOM checks above are historical evidence only, not commands to rerun. `scripts/test-browser-smoke.py` was removed; browser checks are no longer part of this task.

## Browser HTTP Basic auth correction (current source/test work complete; no deployment/browser proof)

- [x] Replace the custom frontend login form with a redirect from `/admin` to `/admin/objects`; retain Caddy's standard Basic dialog as the only hosted browser login.
- [x] Remove frontend JWT-cookie read/write/header machinery, its cookie helper/tests, and the fake logout UI; preserve `frontend/config.ts` and real Bearer API-client support.
- [x] Make browser requests same-origin and let the browser manage Basic `Authorization`; forward the incoming `Authorization` only from SSR to the configured internal API target.
- [x] Add FastAPI Basic authentication through the existing user service and preserve Bearer JWT authentication; malformed or invalid Basic credentials must fail as unauthenticated.
- [x] Keep hosted Caddy Basic protection and original `Authorization` forwarding; remove the obsolete custom public JWT header override without adding credentials to source.
- [x] Update current auth documentation and superseded auth records; state that browser credential caching is user-agent controlled and has no 30-day guarantee.
- [x] Add frontend unit and backend HTTP tests using mocked services/session only; run focused tests without containers or browser automation/screenshots. Frontend: `npm test` (17/17); backend: `uv run --with-requirements requirements.txt --with httpx -- python -m unittest discover -s tests -v` (8/8).

## Production frontend runtime correction (current)
- [x] Replace the Docker development-server command with a bounded production Nitro build/runtime image; keep `npm run dev` for local development.
- [x] Resolve production `/api/**` and `/uploads/**` targets from runtime `API_PROXY_TARGET` or `NUXT_API_TARGET`, preserving request path, query, method, body, and auth headers instead of freezing localhost route rules at build time.
- [x] Add focused regression checks for runtime target selection and production proxy routing; verify with a bounded build and HTTP-only candidate/server checks. Browser automation and screenshots remain forbidden.
- [x] Mount create/edit object forms with a Vue custom renderer and mocked component/API dependencies; verify lifecycle requests, edit-data loading and rendered fields without a browser or DOM automation.
- [x] Update frontend runtime docs and record the exact cause uncertainty: the hosted development-only `ce` exception has not been independently reproduced without browser execution.

Verification evidence (2026-11-25): `npm test` passed 21/21; `NODE_OPTIONS=--max-old-space-size=1536 npm run build` completed with exit 0 including Nitro; `node --experimental-strip-types --test tests/objectFormMount.test.mjs` mounted create and edit modes and verified statuses/object requests plus loaded edit fields. Production `node .output/server/index.mjs` HTTP smoke against a local synthetic Node API verified create/edit SSR route HTML, runtime `API_PROXY_TARGET`, runtime `NUXT_API_TARGET`, API query/method/body/Authorization forwarding, synthetic multipart photo body/boundary forwarding, `/uploads` path/query forwarding, and SSR Authorization forwarding. `npm ls vue @vue/runtime-dom @vue/runtime-core --all` resolved one deduped Vue/runtime tree at 3.5.17. The exact hosted client-side `Cannot read properties of null (reading 'ce')` cause remains unproven; no browser automation, Playwright, screenshots, or UI-click claim was made.

- [x] Deploy production source f224643 through Dokploy; process is node .output/server/index.mjs. Create/edit routes return form fields over HTTPS; statuses/object API200. No Vite dev client in HTML. 21 unit/component tests and bounded build passed. Exact prior client ce exception remains unreproduced without forbidden browser checks; no hydration claim.
- [x] Include both verified demo URLs and explicitly requested temporary access details in README and PR descriptions.
