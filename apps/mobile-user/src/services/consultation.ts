import { request } from './api'

export type ConsultationRiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'
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
  risk_level?: ConsultationRiskLevel | null
  care_advice?: string | null
  hospital_advice?: string | null
  high_risk_alert?: string | null
  disclaimer?: string | null
  analysis_status?: string | null
  created_at?: string | null
}

export type ConsultationDoctorReply = {
  message_id: number
  doctor_id: number
  doctor_name: string
  content: string
  suggest_offline_visit: number
  suggest_follow_up: number
  doctor_remark?: string | null
  created_at: string
}

export type ConsultationDoctor = {
  doctor_id: number
  doctor_name: string
  department?: string | null
  title_name?: string | null
}

export type ConsultationMessage = {
  message_id: number
  sender_role: 'USER' | 'DOCTOR' | 'ADMIN'
  sender_id?: number | null
  message_type: string
  content: string
  created_at: string
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
  risk_level?: ConsultationRiskLevel | null
  need_doctor_review: number
  submitted_at?: string | null
  images: ConsultationImage[]
  ai_result?: ConsultationAIResult | null
  doctor_reply?: ConsultationDoctorReply | null
  doctor?: ConsultationDoctor | null
}

export type ConsultationSummary = {
  case_id: number
  case_no: string
  summary_title: string
  status: ConsultationStatus
  risk_level?: ConsultationRiskLevel | null
  need_doctor_review: number
  submitted_at?: string | null
  ai_result?: ConsultationAIResult | null
  doctor_reply?: ConsultationDoctorReply | null
}

export type ConsultationListResponse = {
  list: ConsultationSummary[]
  total: number
  page: number
  page_size: number
}

export type UserNotification = {
  notification_id: number
  title: string
  content: string
  notification_type: string
  related_business_type?: string | null
  related_business_id?: number | null
  read_flag: number
  created_at: string
}

export type UserNotificationListResponse = {
  list: UserNotification[]
  total: number
  page: number
  page_size: number
}

export type CreateConsultationPayload = {
  chief_complaint: string
  onset_duration: string
  itch_level: number
  pain_level: number
  spread_flag: number
  need_doctor_review: number
  image_urls: string[]
}

export type CreateConsultationResponse = {
  consultation: ConsultationDetail
  ai_result?: ConsultationAIResult | null
}

export async function createConsultation(payload: CreateConsultationPayload) {
  return request<CreateConsultationResponse>('/consultations', {
    method: 'POST',
    data: payload,
  })
}

export async function fetchConsultationDetail(caseId: number) {
  return request<ConsultationDetail>(`/consultations/${caseId}`)
}

export async function fetchConsultationMessages(caseId: number) {
  return request<ConsultationMessage[]>(`/consultations/${caseId}/messages`)
}

export async function sendConsultationMessage(caseId: number, content: string, messageType = 'TEXT') {
  return request<{ message_id: number }>(`/consultations/${caseId}/messages`, {
    method: 'POST',
    data: {
      message_type: messageType,
      content,
    },
  })
}

export async function fetchMyConsultations(page = 1, pageSize = 10) {
  return request<ConsultationListResponse>(`/consultations/my?page=${page}&page_size=${pageSize}`)
}

export async function deleteConsultation(caseId: number) {
  return request<{ case_id: number }>(`/consultations/${caseId}`, {
    method: 'DELETE',
  })
}

export async function fetchUserNotifications(page = 1, pageSize = 10) {
  return request<UserNotificationListResponse>(`/user/notifications?page=${page}&page_size=${pageSize}`)
}

export function getConsultationStatusLabel(status?: string | null) {
  const labelMap: Record<string, string> = {
    PENDING_AI: '待分析',
    AI_DONE: '已完成分析',
    WAIT_DOCTOR: '待医生回复',
    DOCTOR_REPLIED: '已回复',
    CLOSED: '已结束',
  }

  return status ? labelMap[status] || status : '处理中'
}

export function getConsultationRiskLabel(risk?: string | null) {
  const labelMap: Record<string, string> = {
    LOW: '低风险',
    MEDIUM: '中风险',
    HIGH: '高风险',
  }

  return risk ? labelMap[risk] || risk : '待评估'
}

export function splitTextSegments(value?: string | null) {
  if (!value) return []

  const normalized = value
    .split(/\r?\n|[；;。]/)
    .map((item) => item.trim().replace(/^[\-\u2022\d.\s]+/, ''))
    .filter(Boolean)

  return normalized.length ? normalized : [value.trim()]
}

export function notificationKind(notification: UserNotification) {
  const text = `${notification.title} ${notification.content}`.toLowerCase()
  if (text.includes('医生')) return 'DOCTOR'
  if (text.includes('分析') || text.includes('风险')) return 'AI'
  return 'SYSTEM'
}
