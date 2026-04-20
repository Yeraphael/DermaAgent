import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { loginControlCenter, type ControlCenterAccount } from '@/data/controlCenter'

const TOKEN_KEY = 'derma-admin-token'
const ACCOUNT_KEY = 'derma-admin-account'

type StoredAccount = ControlCenterAccount | null

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const account = ref<StoredAccount>(
    localStorage.getItem(ACCOUNT_KEY)
      ? (JSON.parse(localStorage.getItem(ACCOUNT_KEY) as string) as ControlCenterAccount)
      : null,
  )

  const isLoggedIn = computed(() => Boolean(token.value))
  const role = computed(() => account.value?.role_type || '')
  const avatar = computed(() => (account.value?.role_type === 'ADMIN'
    ? 'data:image/svg+xml;charset=UTF-8,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22 viewBox=%220 0 120 120%22%3E%3Cdefs%3E%3ClinearGradient id=%22g%22 x1=%220%25%22 y1=%220%25%22 x2=%22100%25%22 y2=%22100%25%22%3E%3Cstop offset=%220%25%22 stop-color=%22%23dbe8ff%22/%3E%3Cstop offset=%22100%25%22 stop-color=%22%23c7d4ff%22/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%22120%22 height=%22120%22 rx=%2236%22 fill=%22url(%23g)%22/%3E%3Ccircle cx=%2260%22 cy=%2244%22 r=%2221%22 fill=%22rgba(255,255,255,.88)%22/%3E%3Cpath d=%22M24 102c6-19 20-29 36-29s30 10 36 29%22 fill=%22rgba(255,255,255,.88)%22/%3E%3C/svg%3E'
    : 'data:image/svg+xml;charset=UTF-8,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22 viewBox=%220 0 120 120%22%3E%3Cdefs%3E%3ClinearGradient id=%22g%22 x1=%220%25%22 y1=%220%25%22 x2=%22100%25%22 y2=%22100%25%22%3E%3Cstop offset=%220%25%22 stop-color=%22%23dbe8ff%22/%3E%3Cstop offset=%22100%25%22 stop-color=%22%23bfeef0%22/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%22120%22 height=%22120%22 rx=%2236%22 fill=%22url(%23g)%22/%3E%3Ccircle cx=%2260%22 cy=%2244%22 r=%2221%22 fill=%22rgba(255,255,255,.88)%22/%3E%3Cpath d=%22M24 102c6-19 20-29 36-29s30 10 36 29%22 fill=%22rgba(255,255,255,.88)%22/%3E%3C/svg%3E'))

  function persist() {
    localStorage.setItem(TOKEN_KEY, token.value)
    localStorage.setItem(ACCOUNT_KEY, JSON.stringify(account.value))
  }

  async function login(username: string, password: string) {
    const data = await loginControlCenter(username, password)
    token.value = data.access_token
    account.value = data.account
    persist()
    return data
  }

  async function loadProfile() {
    return account.value
  }

  function logout() {
    token.value = ''
    account.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(ACCOUNT_KEY)
  }

  return { token, account, avatar, role, isLoggedIn, login, loadProfile, logout }
})
