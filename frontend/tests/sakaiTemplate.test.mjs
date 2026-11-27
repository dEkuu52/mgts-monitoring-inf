import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const expectedFiles = {
  'assets/styles.scss': '310058fa3fd5326ef04be4b2bd2ac074ecf5e1a957d7f04bc40885c2d67c7a3e',
  'assets/tailwind.css': 'cecd141e54e876ffb10459245be5ae92622593b835012068c51c3dbf6cb51afb',
  'assets/layout/_core.scss': '80e5c02a47dccfc5c5e67b582bdbbd8faf33dbcc74b67665dd3a587734f619ae',
  'assets/layout/_footer.scss': '960b4296b557de194ff4f3bbafcb7877876312fa521c279e248b0fdbb9b5aac0',
  'assets/layout/_main.scss': '1da1067139d6cd0bb1c3968eacea2058a2041c389b3163e3a713c0c7ec9fed9e',
  'assets/layout/_menu.scss': '891ee8a6f877620e339101046f0f8355c16b7da38970dd1abbd6812aae71ce72',
  'assets/layout/_mixins.scss': '5bafe7af59220c7e2a5011013d66078d8bffe6e2f59a0f9d67150e74025df2c4',
  'assets/layout/_preloading.scss': '11e4e8f28717cac2ccfb714097a9b36b2ad3bdf676ababa35d811c8f81bfba6c',
  'assets/layout/_responsive.scss': '915fb60804757a309433fd6b00f4174aa66486dbf0e72e915b6b422cc1bc0121',
  'assets/layout/_topbar.scss': '79c8a12a57751f27d4425eb12bf99057e76ed268fdb85bf55913683f666ec27b',
  'assets/layout/_typography.scss': 'ff373d43902621b1d708f19fc641477b47ea64246be62d1ddfda250beaac5fc8',
  'assets/layout/_utils.scss': '7773afbd061cab2169ba2f66b7d86f4649803f9c89057b60a71f9234e375d64b',
  'assets/layout/layout.scss': 'ebb6e0945efd9a42fec1c3562e8093d9311c66107f4fef2d149750734f270c9d',
  'assets/layout/variables/_common.scss': '10e22b75daec188ed174ab927771da5f2e5fb499f5072469437bbac79ca07a0d',
  'assets/layout/variables/_dark.scss': 'c02e2e49559cd7aefe0e96f0e14cc07f1143e44a2d892820316a3482668cac41',
  'assets/layout/variables/_light.scss': '0f5ccb8117fe8269dad6a37b540afb9d84e38bfeb9431191534b2d987a0be6fc',
  'assets/demo/demo.scss': '4a00239351828d2fd2ad61522d413f467f34b7b47e6e4dfb54d13b89ea674e33',
  'assets/demo/code.scss': '837c1909af14187c69f9be7199f6aa136df6b9dbb7ccba89b0062e8f3a56c6c8',
  'assets/demo/flags/flags.css': 'b7c69eec6878ad1a18d5f9a29e422ee4ae235f98d973008ffc51f524545e590b',
}

const expectedAdaptations = {
  'components/sakai/AppLayout.vue': ['src/layout/AppLayout.vue', '14f4550c753cf4e382a0e4fada65120ea3579e57ae27f4164dbe7d7d464e3923'],
  'components/sakai/AppTopbar.vue': ['src/layout/AppTopbar.vue', '592c4a42a66ece55f4f067be9ee8288a776ea69d858845e7849ec15141bcddbc'],
  'components/sakai/AppSidebar.vue': ['src/layout/AppSidebar.vue', '6ebbf80f6bf4b3fd715351ceb5c3d4622a7520f544383ebb2f1764696fc21995'],
  'components/sakai/AppMenu.vue': ['src/layout/AppMenu.vue', '92315d81c42a65a2c5ab25b7fb528438a77d55d0086a0bff558589217930593e'],
  'components/sakai/AppMenuItem.vue': ['src/layout/AppMenuItem.vue', 'b5eba3abd2787962041526be28eb2fcdf96ee263b681b6509873206075cb6aad'],
  'components/sakai/AppFooter.vue': ['src/layout/AppFooter.vue', 'd18fac8e21c74fe2e5e5620d4a094640aaf7d306e032709acbc79ddc9ab91358'],
  'composables/sakai/useSakaiLayout.ts': ['src/layout/composables/layout.js', '7bdb0bab6bbe8abd41acaf49a7b68236eec34636493b5b429d8c4d8ae87d557e'],
}

test('Sakai assets are unmodified copies from the pinned upstream commits', async () => {
  const manifest = JSON.parse(await readFile(new URL('../sakai-template-manifest.json', import.meta.url), 'utf8'))

  assert.equal(manifest.template.repository, 'https://github.com/primefaces/sakai-vue')
  assert.equal(manifest.template.version, '5.0.0')
  assert.equal(manifest.template.revision, 'ec6b6ef53ad4fa7f2861277f50f2d9e236c40372')
  assert.equal(manifest.assets.repository, 'https://github.com/primefaces/sakai-assets')
  assert.equal(manifest.assets.revision, 'eaa70ece4cfa9aeb8f60b36dce5a422b6bae8003')
  assert.equal(manifest.license, 'MIT')
  assert.equal(manifest.licenseFile.target, 'licenses/SAKAI-MIT-LICENSE.md')
  assert.equal(manifest.licenseFile.sha256, 'cd6426739ea0d1bf7b6692f54563165fa6bd3f2cd236aa82f9fc2a01de37f193')
  const license = await readFile(new URL('../licenses/SAKAI-MIT-LICENSE.md', import.meta.url))
  assert.equal(createHash('sha256').update(license).digest('hex'), manifest.licenseFile.sha256)

  const entries = new Map(manifest.files.map(file => [file.target, file]))
  assert.deepEqual([...entries.keys()].sort(), Object.keys(expectedFiles).sort())

  for (const [target, expectedHash] of Object.entries(expectedFiles)) {
    const entry = entries.get(target)
    assert.equal(entry.sha256, expectedHash, `${target} manifest hash`)
    const bytes = await readFile(new URL(`../${target}`, import.meta.url))
    assert.equal(createHash('sha256').update(bytes).digest('hex'), expectedHash, `${target} upstream bytes`)
  }

  const adaptations = new Map(manifest.adaptations.map(file => [file.target, file]))
  assert.deepEqual([...adaptations.keys()].sort(), Object.keys(expectedAdaptations).sort())
  for (const [target, [source, sourceSha256]] of Object.entries(expectedAdaptations)) {
    assert.deepEqual(
      { source: adaptations.get(target).source, sourceSha256: adaptations.get(target).sourceSha256 },
      { source, sourceSha256 },
      `${target} source provenance`,
    )
    await readFile(new URL(`../${target}`, import.meta.url))
  }
})

test('the imported Sakai source map and license are documented', async () => {
  const provenance = await readFile(new URL('../SAKAI_TEMPLATE.md', import.meta.url), 'utf8')

  assert.match(provenance, /ec6b6ef53ad4fa7f2861277f50f2d9e236c40372/)
  assert.match(provenance, /eaa70ece4cfa9aeb8f60b36dce5a422b6bae8003/)
  assert.match(provenance, /SAKAI-MIT-LICENSE\.md/)
  assert.match(provenance, /sakai-template-manifest\.json/)
})

test('Nuxt loads Sakai global styles, default Aura, and the official Tailwind v4 Vite plugin', async () => {
  const nuxtConfig = await readFile(new URL('../nuxt.config.ts', import.meta.url), 'utf8')
  const styleEntry = await readFile(new URL('../scss/main.scss', import.meta.url), 'utf8')
  const packageJson = JSON.parse(await readFile(new URL('../package.json', import.meta.url), 'utf8'))

  assert.match(styleEntry, /@use ["']@\/assets\/styles\.scss["'];/)
  assert.doesNotMatch(styleEntry, /\.admin-shell|\.workspace-topbar|\.page-panel|\.login-shell/)
  assert.match(nuxtConfig, /tailwindcss\(\)/)
  assert.match(nuxtConfig, /'@\/assets\/tailwind\.css'/)
  assert.match(nuxtConfig, /preset:\s*Aura/)
  assert.doesNotMatch(nuxtConfig, /MGTSAura|definePreset/)
  assert.ok(packageJson.devDependencies['@tailwindcss/vite'])
  assert.ok(packageJson.devDependencies.tailwindcss)
  assert.ok(packageJson.dependencies['tailwindcss-primeui'])
})

test('Sakai layout state uses Nuxt request-scoped state instead of module-level reactive singletons', async () => {
  const layoutState = await readFile(new URL('../composables/sakai/useSakaiLayout.ts', import.meta.url), 'utf8')
  const adminMenu = await readFile(new URL('../components/sakai/AppMenu.vue', import.meta.url), 'utf8')
  const adminLayout = await readFile(new URL('../layouts/admin.vue', import.meta.url), 'utf8')
  const navigation = await readFile(new URL('../components/sakai/navigation.ts', import.meta.url), 'utf8')
  const topbar = await readFile(new URL('../components/sakai/AppTopbar.vue', import.meta.url), 'utf8')

  assert.match(layoutState, /useState(?:<[^>]+>)?\(/)
  assert.doesNotMatch(layoutState, /^(?:const|let)\s+\w+\s*=\s*reactive\(/m)
  assert.match(adminMenu, /aria-label="Основная навигация"/)
  for (const label of ['Пользователи', 'Объекты', 'Дефекты', 'Статусы', 'Карта']) {
    assert.ok(navigation.includes(label), `navigation label ${label}`)
  }
  assert.doesNotMatch(topbar, /logout|Выйти|\/api\/logout/i)
  assert.match(adminLayout, /AppLayout/)
})

test('shell explicitly imports its nested composable instead of assuming recursive Nuxt auto-imports', async () => {
  for (const component of ['AppLayout.vue', 'AppTopbar.vue', 'AppMenuItem.vue']) {
    const source = await readFile(new URL(`../components/sakai/${component}`, import.meta.url), 'utf8')
    assert.match(source, /import\s+\{\s*useSakaiLayout\s*\}\s+from\s+['"]~\/composables\/sakai\/useSakaiLayout['"]/)
  }
})

test('unused legacy site layout cannot reintroduce unresolved stylesheet imports', async () => {
  await assert.rejects(readFile(new URL('../layouts/site.vue', import.meta.url)), { code: 'ENOENT' })
})
