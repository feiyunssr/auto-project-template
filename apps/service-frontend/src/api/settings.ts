import { request } from './http'
import type { AiProfile } from './types'

export function fetchAiProfiles(headers: Record<string, string>, scenarioKey?: string) {
  const query = scenarioKey ? `?scenario_key=${encodeURIComponent(scenarioKey)}` : ''
  return request<{ items: AiProfile[] }>(`/settings/ai-profiles${query}`, {}, headers)
}

export function saveAiProfile(headers: Record<string, string>, payload: Record<string, unknown>) {
  return request<AiProfile>('/settings/ai-profiles', { method: 'POST', body: JSON.stringify(payload) }, headers)
}
