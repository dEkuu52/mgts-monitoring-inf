import assert from 'node:assert/strict'
import { readFile, readdir } from 'node:fs/promises'
import test from 'node:test'

const frontendRoot = new URL('../', import.meta.url)
const legacyPageClasses = /\b(?:login-shell|login-card|login-brand|login-brand__name|login-eyebrow|login-form|login-footer|login-help|login-intro|page-panel|page-heading(?:__\w+)?|entity-form(?:__\w+|--\w+)?|form-field|form-control|data-table|table-empty|table-message|muted-value|photo-section(?:__\w+)?|photo-workspace|photo-preview(?:__\w+)?|photo-empty(?:__\w+)?|photo-controls(?:__\w+)?|photo-drop-overlay(?:__\w+)?|processed-photo(?:__\w+)?|object-thumb|visually-hidden-file-input)\b/

async function readTree(path) {
  const entries = await readdir(new URL(path, frontendRoot), { withFileTypes: true })
  return Promise.all(entries.map(async entry => {
    const relativePath = `${path}/${entry.name}`
    if (entry.isDirectory()) return readTree(relativePath)
    return readFile(new URL(relativePath, frontendRoot), 'utf8').then(content => ({ path: relativePath, content }))
  })).then(groups => groups.flat())
}

test('admin pages and tables use Sakai page, table, and form utilities instead of handcrafted class hooks', async () => {
  const files = [
    ...(await readTree('pages/admin')),
    ...(await readTree('components/tables')),
  ]

  assert.ok(files.length > 0)
  for (const file of files) {
    assert.doesNotMatch(file.content, legacyPageClasses, `${file.path} contains a removed handcrafted page class`)
    assert.doesNotMatch(file.content, /<style\b/, `${file.path} must use the shared Sakai utility system`)
  }

  const tableSources = files.filter(file => file.path.includes('/tables/'))
  for (const file of tableSources) {
    assert.match(file.content, /<DataTable\b/, `${file.path} retains the PrimeVue data table`)
    assert.match(file.content, /\bcard\b/, `${file.path} uses the Sakai card recipe`)
  }
})

test('admin entry route redirects to objects instead of collecting credentials', async () => {
  const adminEntry = await readFile(new URL('pages/admin/index.vue', frontendRoot), 'utf8')

  assert.match(adminEntry, /await navigateTo\('\/admin\/objects',\s*\{\s*redirectCode:\s*302\s*\}\)/)
  assert.doesNotMatch(adminEntry, /<form|password|username|\/api\/auth\/login|useCookie\(['"]token/)
})

test('list pages retain their established API routes, row actions, sorting, and pagination', async () => {
  const tables = [
    ['objectsTable.vue', '/api/infrastructure-objects', '/admin/objects/action', 'objects'],
    ['findingsTable.vue', '/api/defects', '/admin/findings/action', 'findings'],
    ['statusesTable.vue', '/api/statuses', '/admin/statuses/action', 'statuses'],
    ['usersTable.vue', '/api/users', '/admin/users/action', 'users'],
  ]

  for (const [filename, api, actionPath, rows] of tables) {
    const source = await readFile(new URL(`components/tables/${filename}`, frontendRoot), 'utf8')
    assert.ok(source.includes(api), `${filename} retains ${api}`)
    assert.ok(source.includes(actionPath), `${filename} retains its existing action route`)
    assert.match(source, new RegExp(`:paginator="${rows}\\.length > 8"`))
    assert.match(source, /:rows="8"/)
    assert.match(source, /:rows-per-page-options="\[8, 16, 32\]"/)
    assert.match(source, /<Column[^>]+sortable/)
  }
})

test('finding, status, and user edit forms retain their CRUD routes and existing fields', async () => {
  const forms = [
    ['findings/action.vue', '/api/defects', ['detection_id', 'defect_type', 'defect_confidence', 'severity', 'recommended_action']],
    ['statuses/action.vue', '/api/statuses', ['type', 'description']],
    ['users/action.vue', '/api/users', ['username', 'email', 'phone', 'role', 'password']],
  ]

  for (const [path, api, fields] of forms) {
    const source = await readFile(new URL(`pages/admin/${path}`, frontendRoot), 'utf8')
    assert.ok(source.includes(api), `${path} retains ${api}`)
    assert.match(source, /method: 'POST'/)
    assert.match(source, /method: 'PUT'/)
    for (const field of fields) {
      assert.match(source, new RegExp(`v-model="fields\\.${field}"`), `${path} retains the ${field} field`)
    }
  }
})

test('object editing retains CRUD fields, photo replacement/removal, and processed-photo status', async () => {
  const objectForm = await readFile(new URL('pages/admin/objects/action.vue', frontendRoot), 'utf8')

  for (const field of ['type', 'external_id', 'place', 'lat', 'lon', 'status_id']) {
    assert.match(objectForm, new RegExp(`source\\.${field}|fields\\.${field}`), `object form retains ${field}`)
  }
  assert.match(objectForm, /method: 'POST',[\s\S]*?body: payload/)
  assert.match(objectForm, /method: 'PUT',[\s\S]*?body: payload/)
  assert.match(objectForm, /\/api\/infrastructure-objects\/\$\{objectId\}\/photo/)
  assert.match(objectForm, /method: 'DELETE'/)
  assert.match(objectForm, /processed_img_url/)
  assert.match(objectForm, /processing_status/)
  assert.match(objectForm, /@change="onPhotoSelected"/)
  assert.match(objectForm, /window\.addEventListener\('drop', onWindowDrop\)/)
})
