import { computed, reactive, readonly } from 'vue'

import { fetchHubAuthenticatedUser, getHubApiBaseUrl } from '../api/hubAuth'
import type { ApiError, HubSession, HubSessionSource } from '../api/types'

function readBooleanEnv(value: string | undefined, fallback: boolean): boolean {
  if (value == null) {
    return fallback
  }
  return ['1', 'true', 'yes', 'on'].includes(value.trim().toLowerCase())
}

const HUB_AUTH_REQUIRED = readBooleanEnv(import.meta.env.VITE_REQUIRE_HUB_AUTH, false)
const HUB_ACCESS_TOKEN_STORAGE_KEY =
  import.meta.env.VITE_HUB_ACCESS_TOKEN_STORAGE_KEY ?? 'auto_project_template_hub_access_token'
const HUB_LOGIN_URL_STORAGE_KEY =
  import.meta.env.VITE_HUB_LOGIN_URL_STORAGE_KEY ?? 'auto_project_template_hub_login_url'

function resolveHubBrowserUrl(rawUrl: string | undefined) {
  if (!rawUrl) {
    return rawUrl
  }
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

const FALLBACK_SESSION: HubSession = {
  hubUserId: import.meta.env.VITE_DEV_HUB_USER_ID ?? 'local-dev-user',
  hubUserName: import.meta.env.VITE_DEV_HUB_USER_NAME ?? 'Local Operator',
  role: import.meta.env.VITE_DEV_HUB_ROLE ?? 'operator',
  loginUrl: resolveHubBrowserUrl(import.meta.env.VITE_HUB_LOGIN_URL),
}

interface HubSessionState {
  session: HubSession | null
  sessionSource: HubSessionSource
  authExpired: boolean
  overlayMessage: string
  redirectPending: boolean
}

interface ResolvedHubSession {
  session: HubSession | null
  source: HubSessionSource
}

interface HandoffPayload {
  accessToken: string | null
  loginUrl: string | null
}

const authExpiredListeners = new Set<() => void>()

const state = reactive<HubSessionState>({
  session: null,
  sessionSource: 'missing',
  authExpired: false,
  overlayMessage: '登录状态已失效，正在返回 Hub 登录页',
  redirectPending: false,
})

function readStoredAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return window.localStorage.getItem(HUB_ACCESS_TOKEN_STORAGE_KEY)
}

function setStoredAccessToken(accessToken: string | null) {
  if (typeof window === 'undefined') {
    return
  }

  if (accessToken) {
    window.localStorage.setItem(HUB_ACCESS_TOKEN_STORAGE_KEY, accessToken)
  } else {
    window.localStorage.removeItem(HUB_ACCESS_TOKEN_STORAGE_KEY)
  }
}

function readStoredLoginUrl(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return window.localStorage.getItem(HUB_LOGIN_URL_STORAGE_KEY)
}

function setStoredLoginUrl(loginUrl: string | null) {
  if (typeof window === 'undefined') {
    return
  }

  if (loginUrl) {
    window.localStorage.setItem(HUB_LOGIN_URL_STORAGE_KEY, loginUrl)
  } else {
    window.localStorage.removeItem(HUB_LOGIN_URL_STORAGE_KEY)
  }
}

function consumeHandoffPayload(): HandoffPayload {
  if (typeof window === 'undefined') {
    return { accessToken: null, loginUrl: null }
  }

  const currentUrl = new URL(window.location.href)
  const searchParams = currentUrl.searchParams
  const hashParams = new URLSearchParams(
    currentUrl.hash.startsWith('#') ? currentUrl.hash.slice(1) : currentUrl.hash,
  )

  const accessToken = hashParams.get('hub_access_token') ?? searchParams.get('hub_access_token')
  const loginUrl = hashParams.get('hub_login_url') ?? searchParams.get('hub_login_url')

  let consumed = false
  for (const key of ['hub_access_token', 'hub_login_url']) {
    if (hashParams.has(key)) {
      hashParams.delete(key)
      consumed = true
    }
    if (searchParams.has(key)) {
      searchParams.delete(key)
      consumed = true
    }
  }

  if (consumed) {
    currentUrl.search = searchParams.toString()
    currentUrl.hash = hashParams.toString()
    window.history.replaceState(
      null,
      '',
      `${currentUrl.pathname}${currentUrl.search}${currentUrl.hash}`,
    )
  }

  return {
    accessToken,
    loginUrl,
  }
}

function buildCurrentRedirectUrl() {
  if (typeof window === 'undefined') {
    return resolveHubBrowserUrl(import.meta.env.VITE_HUB_LOGIN_URL) ?? '/login'
  }

  const redirectUrl = new URL(window.location.href)
  redirectUrl.hash = ''
  redirectUrl.searchParams.delete('hub_access_token')
  redirectUrl.searchParams.delete('hub_login_url')
  return redirectUrl.toString()
}

function buildLoginUrl() {
  const rawLoginUrl =
    resolveHubBrowserUrl(state.session?.loginUrl) ??
    readStoredLoginUrl() ??
    resolveHubBrowserUrl(import.meta.env.VITE_HUB_LOGIN_URL) ??
    '/login'
  try {
    const loginUrl = new URL(rawLoginUrl, window.location.origin)
    loginUrl.searchParams.set('redirect_url', buildCurrentRedirectUrl())
    return loginUrl.toString()
  } catch {
    return rawLoginUrl
  }
}

function readFallbackSession(): ResolvedHubSession {
  if (!HUB_AUTH_REQUIRED) {
    return { session: { ...FALLBACK_SESSION }, source: 'local_fallback' }
  }
  return { session: null, source: 'missing' }
}

async function readHubSession(): Promise<ResolvedHubSession> {
  const injected = window.__HUB_SESSION__
  if (injected?.hubUserId) {
    const resolvedLoginUrl = resolveHubBrowserUrl(
      injected.loginUrl ?? readStoredLoginUrl() ?? import.meta.env.VITE_HUB_LOGIN_URL,
    )
    setStoredLoginUrl(resolvedLoginUrl ?? null)
    return {
      session: {
        hubUserId: injected.hubUserId,
        hubUserName: injected.hubUserName,
        role: injected.role,
        loginUrl: resolvedLoginUrl,
      },
      source: 'hub',
    }
  }

  const handoff = consumeHandoffPayload()
  if (handoff.accessToken) {
    setStoredAccessToken(handoff.accessToken)
  }
  if (handoff.loginUrl) {
    setStoredLoginUrl(resolveHubBrowserUrl(handoff.loginUrl) ?? handoff.loginUrl)
  }

  const accessToken = handoff.accessToken ?? readStoredAccessToken()
  if (!accessToken || !getHubApiBaseUrl()) {
    return readFallbackSession()
  }

  try {
    const response = await fetchHubAuthenticatedUser(accessToken)
    const resolvedLoginUrl = resolveHubBrowserUrl(
      handoff.loginUrl ?? readStoredLoginUrl() ?? import.meta.env.VITE_HUB_LOGIN_URL,
    )
    setStoredLoginUrl(resolvedLoginUrl ?? null)
    return {
      session: {
        hubUserId: response.user.user_id,
        hubUserName: response.user.display_name ?? response.user.username,
        role: response.roles[0] ?? 'operator',
        loginUrl: resolvedLoginUrl,
      },
      source: 'hub',
    }
  } catch {
    setStoredAccessToken(null)
    return readFallbackSession()
  }
}

function encodeHeaderValue(value: string) {
  const bytes = new TextEncoder().encode(value)
  let binary = ''
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte)
  })
  return window.btoa(binary)
}

function scheduleRedirect() {
  if (!HUB_AUTH_REQUIRED) {
    return
  }
  if (state.redirectPending) {
    return
  }

  state.redirectPending = true
  window.setTimeout(() => {
    window.location.href = buildLoginUrl()
  }, 1000)
}

function notifyAuthExpired() {
  authExpiredListeners.forEach((listener) => listener())
}

function expireSession(message: string) {
  setStoredAccessToken(null)
  state.authExpired = true
  state.overlayMessage = message
  notifyAuthExpired()
  scheduleRedirect()
}

async function bootstrapSession() {
  const resolved = await readHubSession()
  state.session = resolved.session
  state.sessionSource = resolved.source
  const session = resolved.session
  if (!session) {
    expireSession('登录状态已失效，正在返回 Hub 登录页')
    return
  }
  state.authExpired = false
  state.redirectPending = false
}

function authHeaders(): Record<string, string> {
  if (!state.session || state.authExpired) {
    return {}
  }

  const headers: Record<string, string> = {
    'x-hub-user-id': state.session.hubUserId,
    'x-hub-role': state.session.role ?? '',
  }

  if (state.session.hubUserName) {
    headers['x-hub-user-name-b64'] = encodeHeaderValue(state.session.hubUserName)
  }

  return headers
}

function handleAuthError(error: Partial<Pick<ApiError, 'code' | 'status'>>) {
  if (!HUB_AUTH_REQUIRED) {
    return false
  }
  if (error.code !== 'AUTH_REQUIRED' && error.status !== 401 && error.status !== 403) {
    return false
  }
  expireSession('当前会话已失效，已暂停提交与刷新操作')
  return true
}

function clearSensitiveRuntime() {
  notifyAuthExpired()
}

export function useHubSessionStore() {
  return {
    state: readonly(state),
    loginUrl: computed(() => buildLoginUrl()),
    isAuthenticated: computed(() => Boolean(state.session?.hubUserId) && !state.authExpired),
    isUsingHubSession: computed(() => state.sessionSource === 'hub' && !state.authExpired),
    isUsingFallbackSession: computed(
      () => state.sessionSource === 'local_fallback' && !state.authExpired,
    ),
    bootstrapSession,
    authHeaders,
    handleAuthError,
    clearSensitiveRuntime,
    onAuthExpired: (listener: () => void) => {
      authExpiredListeners.add(listener)
      return () => authExpiredListeners.delete(listener)
    },
  }
}
