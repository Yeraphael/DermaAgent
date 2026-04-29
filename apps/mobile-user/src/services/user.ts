import { request } from './api'
import { getSession, setSession } from './session'

export type UserProfileBundle = {
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

export type UserProfileUpdatePayload = {
  real_name?: string
  gender?: string
  age?: number | null
  birthday?: string | null
  city?: string
  occupation?: string
  emergency_contact?: string
  emergency_phone?: string
  remark?: string
  avatar_url?: string
}

export type HealthProfileUpdatePayload = {
  allergy_history?: string
  past_medical_history?: string
  medication_history?: string
  skin_type?: string
  skin_sensitivity?: string
  sleep_pattern?: string
  diet_preference?: string
  special_notes?: string
}

export type HealthArchiveResponse = {
  stats: {
    skin_type: string
    skin_type_updated_at?: string | null
    consultations_30d: number
    consultations_30d_delta: number
    doctor_replies_total: number
    doctor_replies_30d: number
    care_plan_status: string
    care_plan_updated_at?: string | null
  }
  basic_info: {
    real_name: string
    gender: string
    age?: number | null
    phone: string
    skin_type: string
  }
  risk_trend: Array<{
    level: 'LOW' | 'MEDIUM' | 'HIGH'
    label: string
    percentage: number
    days: number
    count: number
  }>
  recent_cases: Array<{
    case_id: number
    case_no: string
    title: string
    submitted_at?: string | null
    status: string
    risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | null
  }>
  care_suggestions: string[]
}

function patchStoredSession(data: Partial<UserProfileBundle>) {
  const current = getSession()
  if (!current) return
  setSession({
    ...current,
    ...data,
  })
}

export async function fetchUserProfileBundle() {
  return request<UserProfileBundle>('/user/profile')
}

export async function updateUserProfile(payload: UserProfileUpdatePayload) {
  const response = await request<{ profile: UserProfileBundle['profile'] }>('/user/profile', {
    method: 'PUT',
    data: payload,
  })
  patchStoredSession({
    profile: {
      ...getSession()?.profile,
      ...response.profile,
    },
  })
  return response
}

export async function updateHealthProfile(payload: HealthProfileUpdatePayload) {
  const response = await request<UserProfileBundle['health_profile']>('/user/health-profile', {
    method: 'PUT',
    data: payload,
  })
  patchStoredSession({ health_profile: response })
  return response
}

export async function fetchHealthArchive() {
  return request<HealthArchiveResponse>('/user/health-archive')
}
