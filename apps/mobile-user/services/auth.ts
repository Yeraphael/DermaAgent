import { clearSession, request, setSession } from '../utils/api'

export async function loginUser(phone: string, password: string) {
  const session = await request<any>('/auth/login', {
    method: 'POST',
    data: {
      username: phone,
      password,
    },
  })
  setSession(session)
  return session
}

export async function sendVerificationCode(phone: string, scene: 'REGISTER' | 'RESET_PASSWORD') {
  return request<{ phone: string; scene: string; expires_in: number }>('/auth/send-code', {
    method: 'POST',
    data: { phone, scene },
  })
}

export async function registerUser(payload: { phone: string; code: string; password: string }) {
  return request('/auth/register', {
    method: 'POST',
    data: {
      username: payload.phone,
      phone: payload.phone,
      verification_code: payload.code,
      password: payload.password,
      confirm_password: payload.password,
      role_type: 'USER',
    },
  })
}

export async function resetPassword(payload: { phone: string; code: string; password: string }) {
  return request('/auth/reset-password', {
    method: 'POST',
    data: {
      phone: payload.phone,
      code: payload.code,
      new_password: payload.password,
      confirm_password: payload.password,
    },
  })
}

export async function changePassword(payload: { oldPassword: string; newPassword: string; confirmPassword: string }) {
  return request('/auth/password', {
    method: 'PUT',
    data: {
      old_password: payload.oldPassword,
      new_password: payload.newPassword,
      confirm_password: payload.confirmPassword,
    },
  })
}

export async function logoutUser() {
  try {
    await request('/auth/logout', { method: 'POST' })
  } catch {
    // Ignore network failures and clear local session anyway.
  } finally {
    clearSession()
  }
}
