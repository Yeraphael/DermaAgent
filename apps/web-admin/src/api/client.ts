import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

type ApiEnvelope<T> = {
  code: number
  message: string
  data: T
  detail?: string
}

export const client = axios.create({
  baseURL,
  timeout: 20000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('derma-admin-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => {
    const payload = response.data as ApiEnvelope<unknown> | unknown
    if (payload && typeof payload === 'object' && 'code' in (payload as ApiEnvelope<unknown>)) {
      const envelope = payload as ApiEnvelope<unknown>
      if (envelope.code !== 0) {
        throw new Error(envelope.message || '请求失败')
      }
      return envelope.data
    }
    return payload
  },
  (error) => {
    const detail = error?.response?.data?.detail || error?.response?.data?.message || error.message
    return Promise.reject(new Error(detail))
  },
)
