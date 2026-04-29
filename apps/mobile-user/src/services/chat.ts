import { request } from './api'

export type ChatSource = {
  title: string
  url: string
  summary: string
}

export type ChatMessage = {
  message_id: number
  role: 'user' | 'assistant'
  content: string
  intent?: string | null
  used_tool: boolean
  tool_name?: string | null
  sources: ChatSource[]
  model_name?: string | null
  created_at: string
}

export type ChatSessionSummary = {
  session_id: number
  title: string
  last_message?: string | null
  updated_at: string
}

export type ChatSessionListResponse = {
  items: ChatSessionSummary[]
}

export type ChatSessionDetail = {
  session_id: number
  title: string
  messages: ChatMessage[]
}

export type ChatMessageResponse = {
  message_id: number
  answer: string
  intent?: string | null
  used_tool: boolean
  tool_name?: string | null
  sources: ChatSource[]
  created_at: string
}

export async function createChatSession(title?: string) {
  return request<{ session_id: number; title: string; created_at: string }>('/chat/sessions', {
    method: 'POST',
    data: title ? { title } : {},
  })
}

export async function fetchChatSessions() {
  return request<ChatSessionListResponse>('/chat/sessions')
}

export async function fetchChatMessages(sessionId: number) {
  return request<ChatSessionDetail>(`/chat/sessions/${sessionId}/messages`)
}

export async function sendChatMessage(sessionId: number, message: string) {
  return request<ChatMessageResponse>(`/chat/sessions/${sessionId}/messages`, {
    method: 'POST',
    data: { message },
  })
}

export async function deleteChatSession(sessionId: number) {
  return request<{ session_id: number }>(`/chat/sessions/${sessionId}`, {
    method: 'DELETE',
  })
}
