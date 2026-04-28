import { getToken } from './session'

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

type RequestOptions = RequestInit & {
  data?: BodyInit | FormData | Record<string, unknown>
}

type Envelope<T> = {
  code?: number
  data?: T
  detail?: string
  message?: string
}

async function parsePayload<T>(response: Response): Promise<Envelope<T> | string | null> {
  const text = await response.text()
  if (!text) return null

  try {
    return JSON.parse(text) as Envelope<T>
  } catch {
    return text
  }
}

export async function request<T = unknown>(url: string, options: RequestOptions = {}) {
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

  const payload = await parsePayload<T>(response)

  if (!response.ok) {
    if (payload && typeof payload === 'object') {
      throw new Error(payload.detail || payload.message || '请求失败')
    }

    throw new Error(typeof payload === 'string' && payload ? payload : '请求失败')
  }

  if (payload && typeof payload === 'object') {
    return payload.data as T
  }

  return payload as T
}

export type UploadedImage = {
  file_name: string
  stored_name: string
  file_size: number
  file_type: string
  file_url: string
}

export async function uploadImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('scene', 'consultation')

  return request<UploadedImage>('/files/upload-image', {
    method: 'POST',
    data: formData,
  })
}
