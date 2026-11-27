import assert from 'node:assert/strict'
import test from 'node:test'
import { readFile } from 'node:fs/promises'
import { resolveApiTarget, resolveProxyTarget } from '../utils/apiProxy.ts'

const frontendRoot = new URL('../', import.meta.url)

test('runtime API target environment takes precedence over Nuxt runtime config', () => {
  assert.equal(
    resolveApiTarget('http://backend:8000/api', 'http://localhost:3001/api'),
    'http://backend:8000/api',
  )
  assert.equal(resolveApiTarget(undefined, 'http://runtime:8000/api'), 'http://runtime:8000/api')
})

test('API and upload forwarding preserve the backend base path and request query', () => {
  assert.equal(
    resolveProxyTarget('http://backend:8000/api', new URL('http://frontend/api/statuses?limit=8')),
    'http://backend:8000/api/statuses?limit=8',
  )
  assert.equal(
    resolveProxyTarget('http://backend:8000/api', new URL('http://frontend/uploads/processed/frame.png?v=2')),
    'http://backend:8000/uploads/processed/frame.png?v=2',
  )
  assert.equal(
    resolveProxyTarget('http://backend:8000/mgts/api', new URL('http://frontend/uploads/frame.png')),
    'http://backend:8000/mgts/uploads/frame.png',
  )
  assert.equal(resolveProxyTarget('http://backend:8000/api', new URL('http://frontend/admin')), null)
})

test('container serves production Nitro and runtime proxy is not frozen in route rules', async () => {
  const [dockerfile, nuxtConfig, middleware, requestSource] = await Promise.all([
    readFile(new URL('Dockerfile', frontendRoot), 'utf8'),
    readFile(new URL('nuxt.config.ts', frontendRoot), 'utf8'),
    readFile(new URL('server/middleware/backend-proxy.ts', frontendRoot), 'utf8'),
    readFile(new URL('services/useRequest.ts', frontendRoot), 'utf8'),
  ])

  assert.match(dockerfile, /npm run build/)
  assert.match(dockerfile, /CMD \["node", "\.output\/server\/index\.mjs"\]/)
  assert.doesNotMatch(dockerfile, /npm run dev/)
  assert.doesNotMatch(nuxtConfig, /routeRules\s*:|devProxy\s*:/)
  assert.match(middleware, /process\.env\.API_PROXY_TARGET/)
  assert.match(middleware, /resolveProxyTarget\(apiTarget, requestUrl\)/)
  assert.match(requestSource, /resolveApiTarget\(process\.env\.API_PROXY_TARGET, runtimeConfig\.apiTarget\)/)
})
