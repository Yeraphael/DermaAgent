const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const STORAGE_KEY = 'derma-mobile-session'

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, any>
}

export function getSession() {
  return uni.getStorageSync(STORAGE_KEY) || null
}

export function setSession(data: any) {
  uni.setStorageSync(STORAGE_KEY, data)
}

export function clearSession() {
  uni.removeStorageSync(STORAGE_KEY)
}

export function getToken() {
  return getSession()?.access_token || ''
}

export function isLoggedIn() {
  return Boolean(getToken())
}

export function ensureLogin() {
  if (!isLoggedIn()) {
    uni.reLaunch({ url: '/pages/login/index' })
    return false
  }
  return true
}

export function request<T = any>(url: string, options: RequestOptions = {}) {
  return new Promise<T>((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${url}`,
      method: options.method || 'GET',
      data: options.data,
      header: {
        Authorization: getToken() ? `Bearer ${getToken()}` : '',
      },
      success: (response) => {
        const data: any = response.data
        if (response.statusCode === 200) {
          resolve(data.data)
          return
        }
        reject(new Error(data?.detail || data?.message || '请求失败，请稍后重试'))
      },
      fail: (error) => reject(error),
    })
  })
}

export function uploadImage(filePath: string) {
  return new Promise<any>((resolve, reject) => {
    uni.uploadFile({
      url: `${API_BASE}/files/upload-image`,
      filePath,
      name: 'file',
      formData: {
        scene: 'consultation',
      },
      header: {
        Authorization: `Bearer ${getToken()}`,
      },
      success: (response) => {
        const data = JSON.parse(response.data)
        if (response.statusCode === 200) {
          resolve(data.data)
          return
        }
        reject(new Error(data?.detail || data?.message || '上传失败，请稍后重试'))
      },
      fail: (error) => reject(error),
    })
  })
}
