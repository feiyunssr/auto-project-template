import { computed, reactive, readonly } from 'vue'

import type { ApiError, HubSession } from '../api/types'

function readBooleanEnv(value: string | undefined, fallback: boolean): boolean {
  if (value == null) {
    return fallback;
  }
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

const HUB_AUTH_REQUIRED = readBooleanEnv(import.meta.env.VITE_REQUIRE_HUB_AUTH, false);
const FALLBACK_SESSION: HubSession = {
  hubUserId: import.meta.env.VITE_DEV_HUB_USER_ID ?? "local-dev-user",
  hubUserName: import.meta.env.VITE_DEV_HUB_USER_NAME ?? "Local Operator",
  role: import.meta.env.VITE_DEV_HUB_ROLE ?? "operator",
  loginUrl: import.meta.env.VITE_HUB_LOGIN_URL,
};

interface HubSessionState {
  session: HubSession | null;
  authExpired: boolean;
  overlayMessage: string;
  redirectPending: boolean;
}

const authExpiredListeners = new Set<() => void>();

const state = reactive<HubSessionState>({
  session: null,
  authExpired: false,
  overlayMessage: "登录状态已失效，正在返回 Hub 登录页",
  redirectPending: false,
});

function readHubSession(): HubSession | null {
  const injected = window.__HUB_SESSION__;
  if (injected?.hubUserId) {
    return {
      hubUserId: injected.hubUserId,
      hubUserName: injected.hubUserName,
      role: injected.role,
      loginUrl: injected.loginUrl,
    };
  }
  if (!HUB_AUTH_REQUIRED) {
    return { ...FALLBACK_SESSION };
  }
  const localId = import.meta.env.VITE_DEV_HUB_USER_ID;
  if (!localId) {
    return null;
  }
  return { ...FALLBACK_SESSION, hubUserId: localId };
}

function scheduleRedirect() {
  if (!HUB_AUTH_REQUIRED) {
    return;
  }
  if (state.redirectPending) {
    return;
  }
  state.redirectPending = true;
  window.setTimeout(() => {
    const loginUrl = state.session?.loginUrl ?? import.meta.env.VITE_HUB_LOGIN_URL ?? "/login";
    window.location.href = loginUrl;
  }, 1000);
}

function notifyAuthExpired() {
  authExpiredListeners.forEach((listener) => listener());
}

function expireSession(message: string) {
  state.authExpired = true;
  state.overlayMessage = message;
  notifyAuthExpired();
  scheduleRedirect();
}

function bootstrapSession() {
  const session = readHubSession();
  state.session = session;
  if (!session) {
    expireSession("登录状态已失效，正在返回 Hub 登录页");
    return;
  }
  state.authExpired = false;
  state.redirectPending = false;
}

function authHeaders(): Record<string, string> {
  if (!state.session || state.authExpired) {
    return {};
  }
  return {
    "x-hub-user-id": state.session.hubUserId,
    "x-hub-user-name": state.session.hubUserName ?? "",
    "x-hub-role": state.session.role ?? "",
  };
}

function handleAuthError(error: Partial<Pick<ApiError, "code" | "status">>) {
  if (!HUB_AUTH_REQUIRED) {
    return false;
  }
  if (error.code !== "AUTH_REQUIRED" && error.status !== 401 && error.status !== 403) {
    return false;
  }
  expireSession("当前会话已失效，已暂停提交与刷新操作");
  return true;
}

function clearSensitiveRuntime() {
  notifyAuthExpired();
}

export function useHubSessionStore() {
  return {
    state: readonly(state),
    isAuthenticated: computed(() => Boolean(state.session?.hubUserId) && !state.authExpired),
    bootstrapSession,
    authHeaders,
    handleAuthError,
    clearSensitiveRuntime,
    onAuthExpired: (listener: () => void) => {
      authExpiredListeners.add(listener);
      return () => authExpiredListeners.delete(listener);
    },
  };
}
