import type { WorkspaceAccount, WorkspaceHealthProfile, WorkspaceProfile } from './auth'
import { client } from './client'

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
export type ConsultationStatus = 'PENDING_AI' | 'AI_DONE' | 'WAIT_DOCTOR' | 'DOCTOR_REPLIED' | 'CLOSED'

export type ConsultationImage = {
  image_id: number
  file_url: string
  file_name: string
}

export type ConsultationAIResult = {
  analysis_id: number
  model_name: string
  prompt_version?: string | null
  image_observation?: string | null
  possible_conditions?: string | null
  possible_conditions_list?: string[]
  risk_level?: RiskLevel | null
  care_advice?: string | null
  care_advice_list?: string[]
  hospital_advice?: string | null
  high_risk_alert?: string | null
  disclaimer?: string | null
  analysis_status?: string | null
  fail_reason?: string | null
  created_at?: string | null
}

export type ConsultationDoctor = {
  doctor_id: number
  doctor_name: string
  department?: string | null
  title_name?: string | null
  hospital_name?: string | null
}

export type ConsultationDoctorReply = {
  message_id: number
  doctor_id: number
  doctor_name: string
  content: string
  first_impression?: string | null
  care_advice?: string | null
  suggest_offline_visit: number
  suggest_follow_up: number
  doctor_remark?: string | null
  created_at: string
  updated_at?: string | null
}

export type ConsultationAIFeedback = {
  feedback_id: number
  doctor_id: number
  ai_accuracy?: string | null
  correction_note?: string | null
  knowledge_gap_note?: string | null
  created_at?: string | null
}

export type PatientBundle = {
  account: WorkspaceAccount
  profile: WorkspaceProfile
  health_profile: WorkspaceHealthProfile
  tags: string[]
  health_score: number
}

export type ConsultationTimelineItem = {
  event: string
  label: string
  time: string
  note: string
}

export type ConsultationDetail = {
  case_id: number
  case_no: string
  summary_title: string
  chief_complaint: string
  onset_duration?: string | null
  itch_level?: number | null
  pain_level?: number | null
  spread_flag: number
  status: ConsultationStatus
  risk_level?: RiskLevel | null
  need_doctor_review: number
  ai_confidence?: number | null
  submitted_at?: string | null
  closed_at?: string | null
  abnormal_flag: number
  abnormal_note?: string | null
  archived_flag: number
  archived_at?: string | null
  images: ConsultationImage[]
  ai_result?: ConsultationAIResult | null
  doctor_reply?: ConsultationDoctorReply | null
  ai_feedback?: ConsultationAIFeedback | null
  doctor?: ConsultationDoctor | null
  patient?: PatientBundle | null
  timeline: ConsultationTimelineItem[]
}

export type PaginatedResult<T> = {
  list: T[]
  total: number
  page: number
  page_size: number
}

export type DoctorDashboard = {
  doctor: {
    doctor_id: number
    doctor_name: string
    department?: string | null
    title_name?: string | null
    hospital_name?: string | null
    audit_status?: string | null
    service_status?: number | null
    specialty?: string | null
  }
  stats: {
    pending_total: number
    processed_today: number
    high_risk_total: number
    ai_feedback_accuracy: number
    replied_total: number
  }
  priority_queue: ConsultationDetail[]
  focus_case?: ConsultationDetail | null
  trend: Array<{ label: string; consultations: number; highRisk: number }>
  high_risk_alerts: Array<{
    case_id: number
    case_no: string
    summary_title: string
    submitted_at?: string | null
    risk_level?: RiskLevel | null
    patient?: PatientBundle | null
    alert?: string | null
  }>
}

export type DoctorPatientListItem = {
  account: Pick<WorkspaceAccount, 'account_id' | 'username' | 'phone' | 'email'>
  profile: Pick<WorkspaceProfile, 'user_id' | 'real_name' | 'gender' | 'age' | 'city' | 'occupation'>
  health_profile: WorkspaceHealthProfile
  tags: string[]
  health_score: number
  latest_case?: ConsultationDetail | null
  recent_case_count: number
}

export type DoctorPatientDetail = {
  account: Pick<WorkspaceAccount, 'account_id' | 'username' | 'phone' | 'email'>
  profile: WorkspaceProfile
  health_profile: WorkspaceHealthProfile
  tags: string[]
  health_score: number
  history_cases: ConsultationDetail[]
  risk_trend: Array<{ label: string; consultations: number; highRisk: number }>
  care_suggestions: string[]
  follow_up_cases: Array<{
    case_id: number
    case_no: string
    summary_title: string
    reply_time: string
  }>
}

export type AdminDashboard = {
  metrics: {
    users_total: number
    doctors_total: number
    consultations_total: number
    high_risk_total: number
    ai_calls_total: number
    active_doctors_today: number
  }
  trend: Array<{ label: string; consultations: number; highRisk: number }>
  runtime: {
    model_status: string
    queue_waiting: number
    avg_response_seconds: number
    error_rate: number
  }
  doctor_overview: Array<{
    doctor_id: number
    doctor_name: string
    department?: string | null
    title_name?: string | null
    service_status: number
    audit_status: string
    response_rate: number
    today_processed: number
    account: WorkspaceAccount
  }>
  pending_doctors: Array<{
    doctor_id: number
    doctor_name: string
    department?: string | null
    title_name?: string | null
    hospital_name?: string | null
    submitted_at: string
    phone: string
  }>
  latest_activities: Array<{
    log_id: number
    module_name: string
    operation_type: string
    operation_desc: string
    created_at: string
    operation_result?: string | null
  }>
  alerts: Array<Record<string, unknown>>
}

export type AdminUserListItem = {
  account: WorkspaceAccount
  profile: WorkspaceProfile
  stats: {
    consultation_total: number
    latest_case_title?: string | null
    latest_case_time?: string | null
  }
}

export type AdminUserDetail = {
  account: WorkspaceAccount
  profile: WorkspaceProfile
  health_profile: WorkspaceHealthProfile
  tags: string[]
  health_score: number
  recent_consultations: ConsultationDetail[]
}

export type AdminDoctorListItem = {
  doctor_id: number
  account: WorkspaceAccount
  doctor_name: string
  department?: string | null
  title_name?: string | null
  hospital_name?: string | null
  specialty?: string | null
  intro?: string | null
  license_no?: string | null
  audit_status: string
  audit_remark?: string | null
  service_status: number
  created_at: string
  stats: {
    consultation_total: number
    response_rate: number
    online_status: string
  }
}

export type AdminDoctorDetail = {
  account: WorkspaceAccount
  doctor: {
    doctor_id: number
    doctor_name: string
    department?: string | null
    title_name?: string | null
    hospital_name?: string | null
    specialty?: string | null
    intro?: string | null
    license_no?: string | null
    audit_status: string
    audit_remark?: string | null
    service_status: number
  }
  stats: {
    consultation_total: number
    reply_total: number
    response_rate: number
    high_risk_total: number
  }
  recent_consultations: ConsultationDetail[]
}

export type ConfigItem = {
  config_id: number
  config_key: string
  config_value: string
  config_group?: string | null
  description?: string | null
  value_type: string
  updated_at: string
}

export type ConfigGroups = {
  groups: Record<string, ConfigItem[]>
  list: ConfigItem[]
}

export type LogsOverview = {
  metrics: {
    login_total: number
    operation_total: number
    ai_call_total: number
    error_total: number
  }
  trend: Array<{ label: string; consultations: number; highRisk: number }>
  recent_logs: Array<{
    log_id: number
    module_name: string
    operation_type: string
    operation_desc: string
    account_id?: number | null
    role_type?: string | null
    request_ip?: string | null
    operation_result?: string | null
    created_at: string
  }>
  alerts: Array<{
    type: string
    title: string
    content: string
    time: string
  }>
  model_calls: Array<{
    record_id: number
    consultation_id: number
    model_name: string
    analysis_status: string
    fail_reason?: string | null
    created_at: string
  }>
}

function toQuery(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    search.set(key, String(value))
  })
  return search.toString()
}

export async function fetchDoctorDashboard() {
  return client.get<DoctorDashboard>('/doctor/dashboard')
}

export async function fetchDoctorConsultations(params: {
  page?: number
  page_size?: number
  status?: string
  risk_level?: string
  keyword?: string
}) {
  return client.get<PaginatedResult<ConsultationDetail>>(`/doctor/consultations?${toQuery(params)}`)
}

export async function fetchDoctorConsultationDetail(caseId: number) {
  return client.get<ConsultationDetail>(`/doctor/consultations/${caseId}`)
}

export async function submitDoctorReply(caseId: number, payload: {
  first_impression?: string
  care_advice?: string
  suggest_offline_visit: number
  suggest_follow_up: number
  doctor_remark?: string
}) {
  return client.post<{ reply_id: number; status: string }>(`/doctor/consultations/${caseId}/reply`, payload)
}

export async function submitDoctorAIFeedback(caseId: number, payload: {
  ai_accuracy: string
  correction_note?: string
  knowledge_gap_note?: string
}) {
  return client.post<{ feedback_id: number }>(`/doctor/consultations/${caseId}/ai-feedback`, payload)
}

export async function fetchDoctorPatients(keyword = '') {
  const query = toQuery({ keyword })
  return client.get<DoctorPatientListItem[]>(`/doctor/patients${query ? `?${query}` : ''}`)
}

export async function fetchDoctorPatientDetail(userId: number) {
  return client.get<DoctorPatientDetail>(`/doctor/patients/${userId}`)
}

export async function fetchAdminDashboard() {
  return client.get<AdminDashboard>('/admin/dashboard')
}

export async function fetchAdminUsers(params: {
  page?: number
  page_size?: number
  keyword?: string
  status?: number | null
}) {
  return client.get<PaginatedResult<AdminUserListItem>>(`/admin/users?${toQuery(params)}`)
}

export async function fetchAdminUserDetail(userId: number) {
  return client.get<AdminUserDetail>(`/admin/users/${userId}`)
}

export async function updateAdminUserStatus(userId: number, status: number) {
  return client.put<{ user_id: number; status: number }>(`/admin/users/${userId}/status`, { status })
}

export async function fetchAdminDoctors(params: {
  page?: number
  page_size?: number
  keyword?: string
  audit_status?: string
  service_status?: number | null
}) {
  return client.get<PaginatedResult<AdminDoctorListItem>>(`/admin/doctors?${toQuery(params)}`)
}

export async function fetchAdminDoctorDetail(doctorId: number) {
  return client.get<AdminDoctorDetail>(`/admin/doctors/${doctorId}`)
}

export async function auditAdminDoctor(doctorId: number, payload: { audit_status: string; audit_remark?: string }) {
  return client.put<{ doctor_id: number; audit_status: string }>(`/admin/doctors/${doctorId}/audit`, payload)
}

export async function updateAdminDoctorStatus(doctorId: number, status: number) {
  return client.put<{ doctor_id: number; service_status: number }>(`/admin/doctors/${doctorId}/status`, { status })
}

export async function fetchAdminConsultations(params: {
  page?: number
  page_size?: number
  status?: string
  risk_level?: string
  keyword?: string
  doctor_id?: number | null
  user_id?: number | null
  archived_flag?: number | null
  abnormal_flag?: number | null
}) {
  return client.get<PaginatedResult<ConsultationDetail>>(`/admin/consultations?${toQuery(params)}`)
}

export async function fetchAdminConsultationDetail(caseId: number) {
  return client.get<ConsultationDetail>(`/admin/consultations/${caseId}`)
}

export async function closeAdminConsultation(caseId: number) {
  return client.post<{ case_id: number; status: string }>(`/admin/consultations/${caseId}/close`)
}

export async function flagAdminConsultation(caseId: number, payload: { abnormal_flag: number; abnormal_note?: string }) {
  return client.put<{ case_id: number; abnormal_flag: number }>(`/admin/consultations/${caseId}/flag`, payload)
}

export async function archiveAdminConsultation(caseId: number, archived_flag: number) {
  return client.put<{ case_id: number; archived_flag: number }>(`/admin/consultations/${caseId}/archive`, { archived_flag })
}

export async function deleteAdminConsultation(caseId: number) {
  return client.delete<{ case_id: number }>(`/admin/consultations/${caseId}`)
}

export async function fetchAdminConfigs() {
  return client.get<ConfigGroups>('/admin/configs')
}

export async function updateAdminConfig(configKey: string, configValue: unknown) {
  return client.put<ConfigItem>(`/admin/configs/${configKey}`, { config_value: configValue })
}

export async function fetchAdminLogsOverview() {
  return client.get<LogsOverview>('/admin/logs/overview')
}
