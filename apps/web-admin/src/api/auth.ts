import { client } from './client'

export type RoleType = 'USER' | 'DOCTOR' | 'ADMIN'

export type WorkspaceAccount = {
  account_id: number
  username: string
  role_type: RoleType
  phone?: string | null
  email?: string | null
  avatar_url?: string | null
  status: number
  last_login_at?: string | null
}

export type WorkspaceProfile = {
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

export type WorkspaceHealthProfile = {
  allergy_history?: string | null
  past_medical_history?: string | null
  medication_history?: string | null
  skin_type?: string | null
  skin_sensitivity?: string | null
  sleep_pattern?: string | null
  diet_preference?: string | null
  special_notes?: string | null
  updated_at?: string | null
}

export type DoctorMeta = {
  doctor_id: number
  doctor_name: string
  department?: string | null
  title_name?: string | null
  hospital_name?: string | null
  specialty?: string | null
  audit_status?: string | null
  service_status?: number | null
}

export type AdminMeta = {
  admin_id: number
  admin_name: string
  job_title?: string | null
  permissions_summary?: string | null
}

export type WorkspaceSession = {
  access_token: string
  token_type: string
  account: WorkspaceAccount
  profile: WorkspaceProfile
  health_profile: WorkspaceHealthProfile
  doctor_info?: DoctorMeta | null
  admin_info?: AdminMeta | null
}

export async function loginWorkspace(username: string, password: string) {
  return client.post<WorkspaceSession>('/auth/login', { username, password })
}

export async function fetchWorkspaceProfile() {
  return client.get<Omit<WorkspaceSession, 'access_token' | 'token_type'>>('/auth/me')
}

export async function updateWorkspaceProfile(payload: {
  real_name?: string
  gender?: string
  age?: number | null
  birthday?: string
  city?: string
  occupation?: string
  avatar_url?: string
  emergency_contact?: string
  emergency_phone?: string
  remark?: string
}) {
  return client.put<{ profile: WorkspaceProfile }>('/user/profile', payload)
}

export async function changeWorkspacePassword(payload: {
  old_password: string
  new_password: string
  confirm_password: string
}) {
  return client.put<{ success: boolean }>('/auth/password', payload)
}

export async function logoutWorkspace() {
  return client.post<{ success: boolean }>('/auth/logout')
}
