# PrimeVue admin workspace

## Why

The existing admin screens use a minimal legacy layout that makes the object and findings workflows difficult to scan. This change adopts PrimeVue 4 with a upstream Sakai administrative shell while preserving the current Russian-language pages and FastAPI integration.

## Scope

- Restyle the admin entry route, navigation, tables, forms, and map placeholder without replacing the current domain workflows.
- Use the existing HTTP Basic challenge as the only browser login UI; `/admin` redirects to `/admin/objects` and the browser controls credential caching.
- Pass the browser's same-origin Basic `Authorization` through to FastAPI, including SSR requests to the configured internal API target. Do not store Basic credentials or JWTs in frontend JavaScript, cookies, or local storage.
- Keep FastAPI `AUTH_REQUIRED=true` support for Basic credentials checked through the existing user service, while preserving Bearer JWT authentication for existing API clients.
- Keep real FastAPI requests as the default. Provide an explicit, opt-in in-memory demo mode for a backend-free walkthrough and clearly label its synthetic data.
- Preserve existing authentication, API, and object-photo behavior.

## Out of scope

- Choosing or implementing a map provider.
- Replacing the standard browser HTTP Basic dialog with a custom application login or logout flow.
- Claiming that demo records or detections represent real monitoring results.

The browser user agent controls how long HTTP Basic credentials remain cached; the application cannot guarantee a 30-day browser session.

## Accepted template correction
Use the actual MIT-licensed primefaces/sakai-vue template, pinned to ec6b6ef53ad4fa7f2861277f50f2d9e236c40372 (5.0.0), as the layout/theme/spacing source. Preserve its layout SCSS and standard Tailwind/PrimeVue page recipes rather than a custom Sakai-inspired design. Adapt only routing/SSR and MGTS navigation/data. Keep Nuxt and developer config, existing FastAPI contracts, photo workflows, explicit demo mode and honest map placeholder. Remove the rejected bespoke shell/styles after mapping retained functionality. Preserve upstream license and record file provenance. No Hookify work.

## Current container-runtime correction
The frontend image must build and serve the Nuxt/Nitro production output; `npm run dev` remains a local development command only. Production API and `/uploads` forwarding must resolve the configured backend at runtime through `API_PROXY_TARGET` or Nuxt's `NUXT_API_TARGET` runtime override. Do not bake the developer `localhost` target into production proxy routes. Keep the configured `/api` base path, original request method/body/query/headers, SSR authorization forwarding, and existing same-origin browser API contract.
