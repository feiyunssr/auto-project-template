import { computed, reactive, readonly } from 'vue'

import { createTask, fetchTaskDetail, fetchTasks, retryTask } from '../api/tasks'
import type { ApiError, TaskDetail, TaskSummary } from '../api/types'
import { useHubSessionStore } from './useHubSessionStore'

export interface TaskCreatePayload {
  scenario_key: string;
  title: string;
  ai_profile_id?: string | null;
  source_channel?: string;
  input_payload: Record<string, unknown>;
}

const state = reactive({
  loadingList: false,
  loadingDetail: false,
  submitting: false,
  listError: "",
  detailError: "",
  createError: "",
  fieldErrors: {} as Record<string, string>,
  filterStatus: "",
  items: [] as TaskSummary[],
  selectedTaskId: "" as string,
  detail: null as TaskDetail | null,
  retryingIds: [] as string[],
  pollingTimer: 0 as number | undefined,
});

let authHookBound = false;

function upsertTask(summary: TaskSummary) {
  const index = state.items.findIndex((item) => item.id === summary.id);
  if (index >= 0) {
    state.items[index] = summary;
  } else {
    state.items.unshift(summary);
  }
}

export function useTaskStore() {
  const sessionStore = useHubSessionStore();

  if (!authHookBound) {
    sessionStore.onAuthExpired(() => {
      stopPolling();
      state.items = [];
      state.detail = null;
      state.selectedTaskId = "";
      state.listError = "";
      state.detailError = "";
      state.createError = "";
      state.fieldErrors = {};
      state.retryingIds = [];
    });
    authHookBound = true;
  }

  async function loadList(status = state.filterStatus, silent = false) {
    if (!silent) {
      state.loadingList = true;
    }
    state.listError = "";
    state.filterStatus = status;
    try {
      const response = await fetchTasks(sessionStore.authHeaders(), status || undefined);
      state.items = response.items;
    } catch (error) {
      const apiError = error as ApiError;
      if (!sessionStore.handleAuthError(apiError)) {
        state.listError = apiError.message;
      }
    } finally {
      state.loadingList = false;
    }
  }

  async function loadDetail(jobId: string, silent = false) {
    if (!silent) {
      state.loadingDetail = true;
      state.selectedTaskId = jobId;
      state.detail = null;
    }
    state.detailError = "";
    try {
      state.detail = await fetchTaskDetail(sessionStore.authHeaders(), jobId);
      state.selectedTaskId = jobId;
      upsertTask(state.detail);
    } catch (error) {
      const apiError = error as ApiError;
      if (!sessionStore.handleAuthError(apiError)) {
        state.detailError = apiError.message;
      }
    } finally {
      state.loadingDetail = false;
    }
  }

  async function createNewTask(payload: TaskCreatePayload) {
    state.submitting = true;
    state.createError = "";
    state.fieldErrors = {};
    try {
      const summary = await createTask(sessionStore.authHeaders(), payload as unknown as Record<string, unknown>);
      upsertTask(summary);
      await loadDetail(summary.id);
      startPolling();
      return summary;
    } catch (error) {
      const apiError = error as ApiError;
      if (!sessionStore.handleAuthError(apiError)) {
        state.createError = apiError.message;
        state.fieldErrors = apiError.field_errors ?? {};
      }
      throw apiError;
    } finally {
      state.submitting = false;
    }
  }

  async function retryExistingTask(jobId: string) {
    state.retryingIds = [...state.retryingIds, jobId];
    try {
      const summary = await retryTask(sessionStore.authHeaders(), jobId);
      upsertTask(summary);
      await loadDetail(jobId);
      startPolling();
    } catch (error) {
      const apiError = error as ApiError;
      if (!sessionStore.handleAuthError(apiError)) {
        state.detailError = apiError.message;
      }
    } finally {
      state.retryingIds = state.retryingIds.filter((id) => id !== jobId);
    }
  }

  function stopPolling() {
    if (state.pollingTimer) {
      window.clearInterval(state.pollingTimer);
      state.pollingTimer = undefined;
    }
  }

  function startPolling() {
    stopPolling();
    state.pollingTimer = window.setInterval(async () => {
      if (!sessionStore.isAuthenticated.value) {
        stopPolling();
        return;
      }
      await loadList(state.filterStatus, true);
      if (state.selectedTaskId) {
        await loadDetail(state.selectedTaskId, true);
      }
    }, 5000);
  }

  return {
    state: readonly(state),
    selectedTask: computed(() => state.detail),
    hasRunningTask: computed(() =>
      state.items.some((item) => item.status === "queued" || item.status === "running"),
    ),
    timeoutRetryTask: computed(() => {
      if (!state.detail) {
        return null;
      }
      if (state.detail.status !== "running" || state.detail.error_code !== "PROVIDER_TIMEOUT_RETRYING") {
        return null;
      }
      return {
        jobNo: state.detail.job_no,
        title: state.detail.title,
        currentAttemptNo: state.detail.current_attempt_no,
        maxRetries: state.detail.max_retries ?? 0,
      };
    }),
    loadList,
    loadDetail,
    createNewTask,
    retryExistingTask,
    startPolling,
    stopPolling,
    closeDetail: () => {
      state.selectedTaskId = "";
      state.detail = null;
      state.detailError = "";
    },
  };
}
