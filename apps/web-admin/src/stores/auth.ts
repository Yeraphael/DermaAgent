import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { client } from '@/api/client'

type Account = {
  account_id: number
  username: string
  role_type: 'USER' | 'DOCTOR' | 'ADMIN'
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('derma-admin-token') || '')
  const account = ref<Account | null>(localStorage.getItem('derma-admin-account') ? JSON.parse(localStorage.getItem('derma-admin-account') as string) : null)

  const isLoggedIn = computed(() => Boolean(token.value))
  const role = computed(() => account.value?.role_type || '')

  function persist() {
    localStorage.setItem('derma-admin-token', token.value)
    localStorage.setItem('derma-admin-account', JSON.stringify(account.value))
  }

  async function login(username: string, password: string) {
    const response = await client.post('/auth/login', { username, password })
    token.value = response.data.access_token
    account.value = response.data.account
    persist()
    return response.data
  }

  async function loadProfile() {
    if (!token.value) return null
    const response = await client.get('/auth/me')
    account.value = response.data.account
    persist()
    return response.data
  }

  function logout() {
    token.value = ''
    account.value = null
    localStorage.removeItem('derma-admin-token')
    localStorage.removeItem('derma-admin-account')
  }

  return { token, account, role, isLoggedIn, login, loadProfile, logout }
})

