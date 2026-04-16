import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'

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
  (response) => response.data,
  (error) => {
    const detail = error?.response?.data?.detail || error?.response?.data?.message || error.message
    return Promise.reject(new Error(detail))
  },
)

