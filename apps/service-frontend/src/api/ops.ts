import { request } from './http'
import type { HealthResponse } from './types'

export function fetchHealth(headers: Record<string, string>) {
  return request<HealthResponse>('/healthz', {}, headers)
}
