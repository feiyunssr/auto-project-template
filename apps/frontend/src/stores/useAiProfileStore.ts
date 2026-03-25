import { reactive, readonly } from "vue";

import { fetchAiProfiles, saveAiProfile } from "../lib/api";
import type { AiProfile } from "../lib/types";
import { useHubSessionStore } from "./useHubSessionStore";

export interface AiProfileDraft {
  profile_key: string;
  profile_name: string;
  scenario_key: string;
  is_default: boolean;
  is_active: boolean;
  provider_name: string;
  model_name: string;
  system_prompt: string;
  prompt_template: string;
  temperature: number;
  max_tokens: number;
  timeout_ms: number;
  max_retries: number;
  concurrency_limit: number;
}

const emptyDraft = (): AiProfileDraft => ({
  profile_key: "default-general",
  profile_name: "Default General Profile",
  scenario_key: "general",
  is_default: true,
  is_active: true,
  provider_name: "mock",
  model_name: "mock-001",
  system_prompt: "",
  prompt_template: "{{ input_payload }}",
  temperature: 0.2,
  max_tokens: 1024,
  timeout_ms: 5000,
  max_retries: 2,
  concurrency_limit: 2,
});

const state = reactive({
  loading: false,
  saving: false,
  error: "",
  drawerOpen: false,
  items: [] as AiProfile[],
  draft: emptyDraft(),
});

export function useAiProfileStore() {
  const sessionStore = useHubSessionStore();

  async function loadProfiles(scenarioKey?: string) {
    state.loading = true;
    state.error = "";
    try {
      const response = await fetchAiProfiles(sessionStore.authHeaders(), scenarioKey);
      state.items = response.items;
      if (!state.drawerOpen && response.items[0]) {
        hydrateDraft(response.items[0]);
      }
    } catch (error) {
      const apiError = error as { message: string; code?: string; status?: number };
      if (!sessionStore.handleAuthError(apiError)) {
        state.error = apiError.message;
      }
    } finally {
      state.loading = false;
    }
  }

  function hydrateDraft(profile?: AiProfile) {
    state.draft = profile
      ? {
          profile_key: profile.profile_key,
          profile_name: profile.profile_name,
          scenario_key: profile.scenario_key,
          is_default: profile.is_default,
          is_active: profile.is_active,
          provider_name: profile.provider_name,
          model_name: profile.model_name,
          system_prompt: profile.system_prompt ?? "",
          prompt_template: profile.prompt_template ?? "",
          temperature: profile.temperature,
          max_tokens: profile.max_tokens,
          timeout_ms: profile.timeout_ms,
          max_retries: profile.max_retries,
          concurrency_limit: profile.concurrency_limit,
        }
      : emptyDraft();
  }

  async function saveDraft() {
    state.saving = true;
    state.error = "";
    try {
      const profile = await saveAiProfile(sessionStore.authHeaders(), state.draft);
      const index = state.items.findIndex((item) => item.id === profile.id);
      if (index >= 0) {
        state.items[index] = profile;
      } else {
        state.items.unshift(profile);
      }
      hydrateDraft(profile);
      state.drawerOpen = false;
    } catch (error) {
      const apiError = error as { message: string; code?: string; status?: number };
      if (!sessionStore.handleAuthError(apiError)) {
        state.error = apiError.message;
      }
    } finally {
      state.saving = false;
    }
  }

  return {
    state: readonly(state),
    loadProfiles,
    hydrateDraft,
    saveDraft,
    openDrawer: (profile?: AiProfile) => {
      hydrateDraft(profile);
      state.drawerOpen = true;
    },
    patchDraft: (patch: Partial<AiProfileDraft>) => {
      state.draft = { ...state.draft, ...patch };
    },
    closeDrawer: () => {
      state.drawerOpen = false;
    },
  };
}
