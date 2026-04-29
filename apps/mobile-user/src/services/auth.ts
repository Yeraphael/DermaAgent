import { request } from './api'
import { clearSession, getSession, setSession } from './session'

export type UserSession = {
  access_token: string
  token_type: string
  account: {
    account_id: number
    username: string
    role_type: string
    phone?: string | null
    email?: string | null
    avatar_url?: string | null
    status: number
  }
  profile: {
    user_id: number
    real_name?: string | null
    gender?: string | null
    age?: number | null
    birthday?: string | null
    city?: string | null
    occupation?: string | null
    avatar_url?: string | null
    phone?: string | null
    email?: string | null
    emergency_contact?: string | null
    emergency_phone?: string | null
    remark?: string | null
  }
  health_profile: {
    allergy_history?: string | null
    past_medical_history?: string | null
    medication_history?: string | null
    skin_type?: string | null
    skin_sensitivity?: string | null
    sleep_pattern?: string | null
    diet_preference?: string | null
    special_notes?: string | null
  }
}

export type RegisterPayload = {
  phone: string
  code: string
  password: string
}

export type PasswordResetPayload = {
  phone: string
  code: string
  password: string
}

export type PasswordChangePayload = {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

export type VerificationScene = 'REGISTER' | 'RESET_PASSWORD'

export async function loginUser(phone: string, password: string) {
  const session = await request<UserSession>('/auth/login', {
    method: 'POST',
    data: { username: phone, password },
  })
  setSession(session)
  return session
}

export async function sendVerificationCode(phone: string, scene: VerificationScene) {
  return request<{ phone: string; scene: string; expires_in: number }>('/auth/send-code', {
    method: 'POST',
    data: { phone, scene },
  })
}

export async function registerUser(payload: RegisterPayload) {
  return request<UserSession>('/auth/register', {
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

export async function resetPassword(payload: PasswordResetPayload) {
  return request<{ success: boolean }>('/auth/reset-password', {
    method: 'POST',
    data: {
      phone: payload.phone,
      code: payload.code,
      new_password: payload.password,
      confirm_password: payload.password,
    },
  })
}

export async function fetchCurrentSession() {
  const response = await request<Omit<UserSession, 'access_token' | 'token_type'>>('/auth/me')
  const current = getSession()
  if (current?.access_token) {
    setSession({
      ...response,
      access_token: current.access_token,
      token_type: current.token_type || 'Bearer',
    })
  }
  return response
}

export async function changePassword(payload: PasswordChangePayload) {
  return request<{ success: boolean }>('/auth/password', {
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
    await request<{ success: boolean }>('/auth/logout', { method: 'POST' })
  } catch {
    // Ignore logout network errors and still clear local credentials.
  } finally {
    clearSession()
  }
}
