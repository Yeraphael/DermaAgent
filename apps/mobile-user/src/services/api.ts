import { getToken } from './session'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

export async function request<T = any>(url: string, options: RequestInit & { data?: any } = {}) {
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  const token = getToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  let body = options.body
  if (options.data !== undefined && !(options.data instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
    body = JSON.stringify(options.data)
  } else if (options.data instanceof FormData) {
    body = options.data
  }
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
    body,
  })
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || '请求失败')
  }
  return payload.data as T
}

export async function uploadImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('scene', 'consultation')
  return request('/files/upload-image', {
    method: 'POST',
    data: formData,
  })
}
