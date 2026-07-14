import { request } from './http'
import { mockChat } from './mockRepository'

const useMock = import.meta.env.VITE_USE_MOCK_API !== 'false'

export function sendChat(payload) {
  return useMock
    ? mockChat(payload)
    : request('/api/chat', { method: 'POST', body: JSON.stringify(payload) })
}
