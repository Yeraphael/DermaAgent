import { request } from '../utils/api'

export async function fetchUserProfileBundle() {
  return request<any>('/user/profile')
}

export async function updateUserProfile(payload: Record<string, any>) {
  return request('/user/profile', {
    method: 'PUT',
    data: payload,
  })
}

export async function updateHealthProfile(payload: Record<string, any>) {
  return request('/user/health-profile', {
    method: 'PUT',
    data: payload,
  })
}

export async function fetchHealthArchive() {
  return request<any>('/user/health-archive')
}
