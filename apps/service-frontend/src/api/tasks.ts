import { request } from './http'
import type { TaskDetail, TaskSummary } from './types'

export function fetchTasks(headers: Record<string, string>, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  return request<{ items: TaskSummary[] }>(`/tasks${query}`, {}, headers)
}

export function fetchTaskDetail(headers: Record<string, string>, jobId: string) {
  return request<TaskDetail>(`/tasks/${jobId}`, {}, headers)
}

export function createTask(headers: Record<string, string>, payload: Record<string, unknown>) {
  return request<TaskSummary>('/tasks', { method: 'POST', body: JSON.stringify(payload) }, headers)
}

export function retryTask(headers: Record<string, string>, jobId: string) {
  return request<TaskSummary>(`/tasks/${jobId}/retry`, { method: 'POST' }, headers)
}
