import assert from 'node:assert/strict'
import test from 'node:test'
import { readFile } from 'node:fs/promises'

const frontendRoot = new URL('../', import.meta.url)
const requestSource = await readFile(new URL('services/useRequest.ts', frontendRoot), 'utf8')
const nuxtConfig = await readFile(new URL('nuxt.config.ts', frontendRoot), 'utf8')
const frontendConfig = await readFile(new URL('config.ts', frontendRoot), 'utf8')
const dokployCompose = await readFile(new URL('../compose.dokploy.yml', frontendRoot), 'utf8')

test('browser requests use same-origin credentials without frontend token storage or header construction', () => {
  assert.match(requestSource, /credentials:\s*'same-origin'/)
  assert.match(requestSource, /let requestUrl = url/)
  assert.doesNotMatch(requestSource, /useCookie|localStorage|sessionStorage|Bearer|apiTokenHeader|X-MGTS-Authorization/)
  assert.doesNotMatch(nuxtConfig, /apiTokenHeader|NUXT_PUBLIC_API_TOKEN_HEADER|X-MGTS-Authorization/)
  assert.match(frontendConfig, /apiUrl:/)
})

test('SSR forwards only the incoming Authorization header to the configured API target', () => {
  assert.match(requestSource, /resolveApiTarget\(process\.env\.API_PROXY_TARGET, runtimeConfig\.apiTarget\)/)
  assert.match(requestSource, /const incomingAuthorization = import\.meta\.server && apiTarget\s*\? useRequestHeaders\(\['authorization'\]\)\.authorization\s*: undefined/)
  assert.match(requestSource, /if \(import\.meta\.server && apiTarget && incomingAuthorization && !hasAuthorization\)[\s\S]*?headers\.Authorization = incomingAuthorization/)
})

test('Dokploy retains gateway Basic auth and forwards the original Authorization unchanged', () => {
  const backend = dokployCompose.slice(dokployCompose.indexOf('  backend:'), dokployCompose.indexOf('  frontend:'))
  const frontend = dokployCompose.slice(dokployCompose.indexOf('  frontend:'), dokployCompose.indexOf('  gateway:'))
  const gateway = dokployCompose.slice(dokployCompose.indexOf('  gateway:'), dokployCompose.indexOf('\nvolumes:'))

  assert.match(backend, /AUTH_REQUIRED:\s*'true'/)
  assert.doesNotMatch(backend, /ports:/)
  assert.doesNotMatch(frontend, /NUXT_PUBLIC_API_TOKEN_HEADER|X-MGTS-Authorization/)
  assert.match(frontend, /ports:\s*!reset \[\]/)
  assert.match(gateway, /basic_auth\s*\{[\s\S]*?\}\s*reverse_proxy frontend:3000/)
  assert.doesNotMatch(gateway, /header_up|X-MGTS-Authorization/)
  assert.doesNotMatch(gateway, /(?:password|secret|token):\s*[^$?{]/i)
})
