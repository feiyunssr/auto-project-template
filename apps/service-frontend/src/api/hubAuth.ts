import { request } from './http'

function resolveHubBrowserUrl(rawUrl: string) {
  if (typeof window === 'undefined') {
    return rawUrl
  }

  try {
    const resolved = new URL(rawUrl, window.location.origin)
    if (
      ['127.0.0.1', 'localhost'].includes(resolved.hostname) &&
      !['127.0.0.1', 'localhost'].includes(window.location.hostname)
    ) {
      resolved.hostname = window.location.hostname
    }
    return resolved.toString()
  } catch {
    return rawUrl
  }
}

const HUB_API_BASE_URL = resolveHubBrowserUrl(import.meta.env.VITE_HUB_API_BASE_URL ?? '').replace(
  /\/$/,
  '',
)

export interface HubAuthenticatedUserResponse {
  user: {
    user_id: string
    username: string
    display_name: string | null
  }
  roles: string[]
}

export function getHubApiBaseUrl() {
  return HUB_API_BASE_URL
}

export function fetchHubAuthenticatedUser(accessToken: string) {
  if (!HUB_API_BASE_URL) {
    throw new Error('VITE_HUB_API_BASE_URL is not configured.')
  }

  return request<HubAuthenticatedUserResponse>(
    `${HUB_API_BASE_URL}/auth/me`,
    {},
    {
      Authorization: `Bearer ${accessToken}`,
    },
  )
}
