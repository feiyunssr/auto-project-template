import type { ApiError } from './types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '')

function buildUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path
  }

  if (path.startsWith('/healthz')) {
    return path
  }

  return `${API_BASE_URL}${path}`
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
  headers: Record<string, string> = {},
): Promise<T> {
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
      ...(init.headers ?? {}),
    },
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiError | null
    throw {
      code: payload?.code ?? 'REQUEST_FAILED',
      message: payload?.message ?? 'Request failed.',
      field_errors: payload?.field_errors ?? {},
      details: payload?.details ?? {},
      status: response.status,
    } satisfies ApiError
  }

  return (await response.json()) as T
}
