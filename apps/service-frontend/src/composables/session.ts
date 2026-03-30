import { useHubSessionStore } from '../stores/useHubSessionStore'

export function useSession() {
  return useHubSessionStore()
}

export async function restoreSession() {
  useHubSessionStore().bootstrapSession()
}
