export function resolveApiTarget(apiProxyTarget: string | undefined, runtimeApiTarget: unknown) {
  return apiProxyTarget || String(runtimeApiTarget || '')
}

export function resolveProxyTarget(apiTarget: string, requestUrl: URL) {
  const { pathname } = requestUrl
  const isApiRequest = pathname === '/api' || pathname.startsWith('/api/')
  const isUploadRequest = pathname === '/uploads' || pathname.startsWith('/uploads/')

  if (!isApiRequest && !isUploadRequest) return null

  const targetUrl = new URL(apiTarget)
  const backendBasePath = targetUrl.pathname.replace(/\/api\/?$/, '').replace(/\/+$/, '')
  if (isApiRequest) {
    const apiBasePath = targetUrl.pathname.replace(/\/+$/, '')
    targetUrl.pathname = `${apiBasePath}${pathname.slice('/api'.length)}`
  } else {
    targetUrl.pathname = `${backendBasePath}${pathname}`
  }
  targetUrl.search = requestUrl.search
  targetUrl.hash = ''

  return targetUrl.toString()
}
