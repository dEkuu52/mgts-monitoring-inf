import { createError, getRequestURL, proxyRequest } from 'h3'
import { resolveApiTarget, resolveProxyTarget } from '~/utils/apiProxy'

export default defineEventHandler((event) => {
  const requestUrl = getRequestURL(event)
  const { pathname } = requestUrl
  const isProxyRequest = pathname === '/api'
    || pathname.startsWith('/api/')
    || pathname === '/uploads'
    || pathname.startsWith('/uploads/')

  if (!isProxyRequest) return

  const runtimeConfig = useRuntimeConfig(event)
  const apiTarget = resolveApiTarget(process.env.API_PROXY_TARGET, runtimeConfig.apiTarget)
  if (!apiTarget) {
    throw createError({ statusCode: 500, statusMessage: 'API proxy target is not configured' })
  }

  const proxyTarget = resolveProxyTarget(apiTarget, requestUrl)
  if (!proxyTarget) return

  return proxyRequest(event, proxyTarget, { streamRequest: true })
})
