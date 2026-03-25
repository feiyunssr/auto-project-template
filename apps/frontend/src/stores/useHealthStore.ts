import { reactive, readonly } from "vue";

import { fetchHealth } from "../lib/api";
import type { HealthResponse } from "../lib/types";
import { useHubSessionStore } from "./useHubSessionStore";

const state = reactive({
  loading: false,
  error: "",
  data: null as HealthResponse | null,
});

let authHookBound = false;

export function useHealthStore() {
  const sessionStore = useHubSessionStore();

  if (!authHookBound) {
    sessionStore.onAuthExpired(() => {
      state.loading = false;
      state.error = "";
      state.data = null;
    });
    authHookBound = true;
  }

  async function loadHealth() {
    state.loading = true;
    state.error = "";
    try {
      state.data = await fetchHealth(sessionStore.authHeaders());
    } catch (error) {
      const apiError = error as { message: string; code?: string; status?: number };
      if (!sessionStore.handleAuthError(apiError)) {
        state.error = apiError.message;
      }
    } finally {
      state.loading = false;
    }
  }

  return {
    state: readonly(state),
    loadHealth,
  };
}
