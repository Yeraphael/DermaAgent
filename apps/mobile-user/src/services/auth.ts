import { request } from './api'
import { clearSession, setSession } from './session'

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

export async function loginUser(username: string, password: string) {
  const session = await request<UserSession>('/auth/login', {
    method: 'POST',
    data: { username, password },
  })
  setSession(session)
  return session
}

export function logoutUser() {
  clearSession()
}
