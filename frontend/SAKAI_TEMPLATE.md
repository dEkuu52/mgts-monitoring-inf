# Sakai Vue template provenance

The admin shell uses the official PrimeVue **Sakai Vue 5.0.0** template, not a
local recreation. The source is pinned to
[`primefaces/sakai-vue`](https://github.com/primefaces/sakai-vue) commit
`ec6b6ef53ad4fa7f2861277f50f2d9e236c40372`. Its `src/assets` submodule is
[`primefaces/sakai-assets`](https://github.com/primefaces/sakai-assets) commit
`eaa70ece4cfa9aeb8f60b36dce5a422b6bae8003`.

## Imported source

`sakai-template-manifest.json` is the machine-readable file map. It records the
source path, destination path, and SHA-256 for every imported stylesheet and
the original MIT license. The stylesheet and asset files listed there are
byte-for-byte copies from the pinned `sakai-assets` revision. The license is
preserved as `licenses/SAKAI-MIT-LICENSE.md`.

The Sakai layout Vue components and layout composable are adapted from the
source paths and hashes in the manifest. Their destinations retain Sakai's
`.layout-*` class structure; no alternative hand-authored shell styles are
kept.

## Nuxt adaptations

- `AppLayout.vue` replaces upstream `router-view` with a Nuxt slot; the pinned
  Sakai `layout.scss` still supplies the shell, sidebar, topbar, menu, footer,
  breakpoint, and layout-token styling.
- `AppMenu.vue` and `AppMenuItem.vue` use `NuxtLink` and the existing MGTS
  routes. They retain the accessible navigation name, active route state, and
  responsive Sakai menu behavior.
- `AppTopbar.vue` replaces demo actions with the MGTS label and theme toggle;
  there is no application logout action because HTTP Basic credentials are
  browser-managed and cannot be reliably cleared by the frontend.
- `/admin` redirects to `/admin/objects`; the hosted Caddy Basic challenge is
  the only browser login UI. Browser requests use same-origin URLs and SSR
  forwards the incoming authorization header only to the configured internal
  API target.
- `useSakaiLayout.ts` ports the source layout state to Nuxt `useState`, avoiding
  module-level reactive state shared between SSR requests. Browser-only APIs
  are called only from client interactions.
- The PrimeVue Sakai Toast host is omitted because this application already
  uses `nuxt-toast`/iziToast for its notifications; the notification API and
  output remain unchanged.
- `nuxt.config.ts` loads the upstream Tailwind v4 source and Vite plugin with
  the PrimeVue utility plugin, uses the default Aura preset, and loads the
  upstream Lato font link. The API proxy, developer defaults, server-only
  authorization forwarding, and demo-mode configuration remain independent of
  the shell.

## Verification

`tests/sakaiTemplate.test.mjs` pins template and asset revisions, checks the
manifest mapping and hashes against the imported bytes, and verifies the Nuxt
theme/plugin and request-scoped state integration. Run it with:

```sh
node --experimental-strip-types --test tests/sakaiTemplate.test.mjs
```

Integration removes the unused legacy `layouts/site.vue` and its empty stylesheet; no route selected that layout. The shell/topbar explicitly import the nested layout composable because Nuxt does not recursively auto-import composables by default.
