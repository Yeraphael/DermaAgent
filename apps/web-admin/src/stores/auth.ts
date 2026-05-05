import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  changeWorkspacePassword,
  fetchWorkspaceProfile,
  loginWorkspace,
  logoutWorkspace,
  type AdminMeta,
  type DoctorMeta,
  type WorkspaceAccount,
  type WorkspaceHealthProfile,
  type WorkspaceProfile,
  type WorkspaceSession,
} from '@/api/auth'

const TOKEN_KEY = 'derma-admin-token'
const SESSION_KEY = 'derma-admin-session'

type StoredSession = {
  token: string
  account: WorkspaceAccount | null
  profile: WorkspaceProfile | null
  health_profile: WorkspaceHealthProfile | null
  doctor_info: DoctorMeta | null
  admin_info: AdminMeta | null
}

function makeAvatarSeed(name: string, role: string) {
  const initials = (name || role || 'U').slice(0, 2)
  const end = role === 'ADMIN' ? '#bfd2ff' : '#bfeeed'
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#dbe8ff"/>
          <stop offset="100%" stop-color="${end}"/>
        </linearGradient>
      </defs>
      <rect width="120" height="120" rx="34" fill="url(#g)"/>
      <circle cx="60" cy="42" r="20" fill="rgba(255,255,255,.88)"/>
      <path d="M24 100c6-18 20-28 36-28s30 10 36 28" fill="rgba(255,255,255,.88)"/>
      <text x="60" y="108" text-anchor="middle" font-size="15" fill="#345d95" font-family="sans-serif">${initials}</text>
    </svg>
  `
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

function loadStoredSession(): StoredSession {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) {
      return {
        token: localStorage.getItem(TOKEN_KEY) || '',
        account: null,
        profile: null,
        health_profile: null,
        doctor_info: null,
        admin_info: null,
      }
    }
    return JSON.parse(raw) as StoredSession
  } catch {
    return {
      token: localStorage.getItem(TOKEN_KEY) || '',
      account: null,
      profile: null,
      health_profile: null,
      doctor_info: null,
      admin_info: null,
    }
  }
}

export const useAuthStore = defineStore('auth', () => {
  const stored = loadStoredSession()
  const token = ref(stored.token || '')
  const account = ref<WorkspaceAccount | null>(stored.account)
  const profile = ref<WorkspaceProfile | null>(stored.profile)
  const healthProfile = ref<WorkspaceHealthProfile | null>(stored.health_profile)
  const doctorInfo = ref<DoctorMeta | null>(stored.doctor_info)
  const adminInfo = ref<AdminMeta | null>(stored.admin_info)

  const isLoggedIn = computed(() => Boolean(token.value))
  const role = computed(() => account.value?.role_type || '')
  const displayName = computed(() => (
    adminInfo.value?.admin_name
    || doctorInfo.value?.doctor_name
    || profile.value?.real_name
    || account.value?.username
    || ''
  ))
  const title = computed(() => {
    if (role.value === 'ADMIN') {
      return adminInfo.value?.job_title || '系统管理员'
    }
    if (role.value === 'DOCTOR') {
      return [doctorInfo.value?.department, doctorInfo.value?.title_name].filter(Boolean).join(' · ') || '医生'
    }
    return '用户'
  })
  const roleLabel = computed(() => (
    role.value === 'ADMIN' ? '管理员'
      : role.value === 'DOCTOR' ? '医生'
        : '用户'
  ))
  const avatar = computed(() => account.value?.avatar_url || makeAvatarSeed(displayName.value, role.value))

  function persist() {
    localStorage.setItem(TOKEN_KEY, token.value)
    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        token: token.value,
        account: account.value,
        profile: profile.value,
        health_profile: healthProfile.value,
        doctor_info: doctorInfo.value,
        admin_info: adminInfo.value,
      }),
    )
  }

  function applySession(data: Partial<WorkspaceSession> & {
    account: WorkspaceAccount
    profile: WorkspaceProfile
    health_profile: WorkspaceHealthProfile
    doctor_info?: DoctorMeta | null
    admin_info?: AdminMeta | null
  }) {
    account.value = data.account
    profile.value = data.profile
    healthProfile.value = data.health_profile
    doctorInfo.value = data.doctor_info || null
    adminInfo.value = data.admin_info || null
    persist()
  }

  async function login(username: string, password: string) {
    const data = await loginWorkspace(username, password)
    if (data.account.role_type === 'USER') {
      throw new Error('普通用户请使用用户端登录')
    }
    token.value = data.access_token
    applySession(data)
    return data
  }

  async function loadProfile() {
    if (!token.value) return null
    const data = await fetchWorkspaceProfile()
    applySession({
      account: data.account,
      profile: data.profile,
      health_profile: data.health_profile,
      doctor_info: data.doctor_info || null,
      admin_info: data.admin_info || null,
    })
    return data
  }

  async function logout() {
    try {
      if (token.value) {
        await logoutWorkspace()
      }
    } finally {
      token.value = ''
      account.value = null
      profile.value = null
      healthProfile.value = null
      doctorInfo.value = null
      adminInfo.value = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(SESSION_KEY)
    }
  }

  async function updatePassword(oldPassword: string, newPassword: string, confirmPassword: string) {
    return changeWorkspacePassword({
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    })
  }

  return {
    token,
    account,
    profile,
    healthProfile,
    doctorInfo,
    adminInfo,
    avatar,
    role,
    roleLabel,
    title,
    displayName,
    isLoggedIn,
    login,
    loadProfile,
    logout,
    updatePassword,
    applySession,
  }
})
