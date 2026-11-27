# Admin workspace

## ADDED Requirements

### Requirement: Existing admin workflows use the PrimeVue workspace shell

The existing Russian-language admin entry route, users, infrastructure objects, findings, statuses, and map-placeholder screens MUST use the PrimeVue-based workspace presentation. Navigation MUST link to the existing sections and identify the active section. Forms and tables MUST retain their existing entity operations and object-photo workflows. The map screen MUST continue to state that no map provider is connected rather than fabricating map data.

#### Scenario: Operator navigates between admin sections

- **WHEN** the operator opens any existing admin section
- **THEN** the workspace shows navigation to users, objects, findings, statuses, and map
- **AND** the active section is identified
- **AND** selecting a section opens its existing route

### Requirement: Real API mode remains the default

The frontend MUST use the existing FastAPI request path unless demo mode is explicitly enabled. Browser API requests MUST use relative same-origin URLs so the browser can send its cached HTTP Basic credentials normally. SSR requests MUST forward only the incoming `Authorization` header and only to the configured internal API target. Endpoint paths and multipart object-photo requests MUST remain compatible.

#### Scenario: Frontend starts without demo mode

- **WHEN** `NUXT_PUBLIC_DEMO_MODE` is unset or not exactly `true`
- **THEN** frontend requests use the existing API request path
- **AND** mock data is not selected

### Requirement: The browser uses the standard HTTP Basic challenge, not an application login

The browser MUST use the existing HTTP Basic authentication challenge as its only login UI. The `/admin` route MUST redirect to `/admin/objects`; it MUST NOT collect or persist credentials or issue a frontend JWT cookie. The frontend MUST NOT store Basic passwords or Bearer tokens in JavaScript state, cookies, or local storage. The UI MUST NOT claim to log out when it cannot clear browser-managed Basic credentials. Credential caching and its duration are controlled by the browser; the application MUST NOT promise a 30-day browser session.

#### Scenario: Operator opens the admin entry route

- **WHEN** the operator navigates to `/admin`
- **THEN** the frontend redirects to `/admin/objects`
- **AND** the browser's standard HTTP Basic dialog remains the only browser login surface

#### Scenario: Operator attempts to leave the workspace

- **WHEN** the operator views an admin page
- **THEN** the interface does not present a fake logout action that cannot reliably clear HTTP Basic credentials

### Requirement: Backend supports Basic browser credentials and existing Bearer API clients

When `AUTH_REQUIRED=true`, protected FastAPI routes MUST authenticate `Authorization: Basic <credentials>` through the existing `user_service.authenticate` and its current user database. Existing valid `Authorization: Bearer <token>` API clients MUST remain supported. Missing, malformed, or invalid Basic credentials MUST be treated as unauthenticated and MUST NOT cause an internal server error.

#### Scenario: Valid Basic browser request reaches a protected endpoint

- **WHEN** a protected endpoint receives valid Basic credentials
- **THEN** FastAPI authenticates the username/password through the existing user service
- **AND** the protected endpoint proceeds

#### Scenario: Invalid or malformed Basic header reaches a protected endpoint

- **WHEN** a protected endpoint receives a missing, malformed, or invalid Basic header
- **THEN** the request is unauthenticated
- **AND** `AUTH_REQUIRED=true` returns an authentication error rather than an internal server error

#### Scenario: Existing API client uses a Bearer JWT

- **WHEN** a protected endpoint receives a valid Bearer JWT
- **THEN** the existing JWT authentication path continues to authenticate the user

### Requirement: Hosted gateway preserves the original Basic authorization header

The hosted Caddy gateway MUST retain its `basic_auth` protection for every routed path and pass the original `Authorization` header upstream unchanged. It MUST NOT replace `Authorization` from a custom public JWT header or introduce an `X-MGTS-Authorization` transport header. Deployment configuration MUST NOT contain credentials.

#### Scenario: Authenticated browser accesses the hosted frontend/API

- **WHEN** the browser completes the gateway's Basic challenge and requests the frontend or a same-origin API route
- **THEN** the gateway remains the access-control boundary
- **AND** the original `Authorization` header is forwarded without an override header

### Requirement: Demo mode is explicit and visibly synthetic

When the public demo-mode flag is exactly `true`, frontend requests MUST be served by the in-memory mock API and MUST NOT call FastAPI. The interface MUST display a notice that demo data are synthetic and are not real AI results. Demo mutations are process-local and may be discarded on restart.

#### Scenario: Operator enables an isolated demo

- **WHEN** the frontend starts with `NUXT_PUBLIC_DEMO_MODE=true`
- **THEN** requests are handled by the mock API
- **AND** a visible notice identifies synthetic data and disabled backend requests
- **AND** object-photo mock upload, replacement, and removal work without a backend

### Requirement: Actual upstream Sakai design, not a custom imitation
The shell, responsive menu, theme and spacing MUST derive from the pinned official Sakai template. Domain pages MUST use its standard card, toolbar, table and form patterns. Only application content, routing and integration may require adaptation; rejected custom layout styling MUST NOT remain as an alternative. Preserve MIT attribution and source revision.

#### Scenario: Template identity is checked
- **WHEN** the imported layout styles and provenance manifest are verified
- **THEN** the pinned upstream source is identifiable and unchanged files match it
- **AND** adaptations are documented and all existing application routes remain available.
