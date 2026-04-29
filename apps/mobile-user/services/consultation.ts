import { request } from '../utils/api'

export async function createConsultation(payload: {
  chief_complaint: string
  onset_duration: string
  itch_level: number
  pain_level: number
  spread_flag: number
  need_doctor_review: number
  image_urls: string[]
}) {
  return request<any>('/consultations', {
    method: 'POST',
    data: payload,
  })
}

export async function fetchConsultationDetail(caseId: number) {
  return request<any>(`/consultations/${caseId}`)
}

export async function fetchMyConsultations(page = 1, pageSize = 20) {
  return request<any>(`/consultations/my?page=${page}&page_size=${pageSize}`)
}

export async function deleteConsultation(caseId: number) {
  return request<any>(`/consultations/${caseId}`, {
    method: 'DELETE',
  })
}
