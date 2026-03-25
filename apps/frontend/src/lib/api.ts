import type { AiProfile, ApiError, HealthResponse, TaskDetail, TaskSummary } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init: RequestInit = {}, headers: Record<string, string> = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...headers,
      ...(init.headers ?? {}),
    },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiError | null;
    throw {
      code: payload?.code ?? "REQUEST_FAILED",
      message: payload?.message ?? "Request failed.",
      field_errors: payload?.field_errors ?? {},
      details: payload?.details ?? {},
      status: response.status,
    } satisfies ApiError;
  }
  return (await response.json()) as T;
}

export function fetchHealth(headers: Record<string, string>) {
  return request<HealthResponse>("/healthz", {}, headers);
}

export function fetchTasks(headers: Record<string, string>, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<{ items: TaskSummary[] }>(`/api/tasks${query}`, {}, headers);
}

export function fetchTaskDetail(headers: Record<string, string>, jobId: string) {
  return request<TaskDetail>(`/api/tasks/${jobId}`, {}, headers);
}

export function createTask(headers: Record<string, string>, payload: Record<string, unknown>) {
  return request<TaskSummary>("/api/tasks", { method: "POST", body: JSON.stringify(payload) }, headers);
}

export function retryTask(headers: Record<string, string>, jobId: string) {
  return request<TaskSummary>(`/api/tasks/${jobId}/retry`, { method: "POST" }, headers);
}

export function fetchAiProfiles(headers: Record<string, string>, scenarioKey?: string) {
  const query = scenarioKey ? `?scenario_key=${encodeURIComponent(scenarioKey)}` : "";
  return request<{ items: AiProfile[] }>(`/api/settings/ai-profiles${query}`, {}, headers);
}

export function saveAiProfile(headers: Record<string, string>, payload: Record<string, unknown>) {
  return request<AiProfile>("/api/settings/ai-profiles", { method: "POST", body: JSON.stringify(payload) }, headers);
}
