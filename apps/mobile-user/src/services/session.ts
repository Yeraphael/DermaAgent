const KEY = 'derma-mobile-session'

export function getSession() {
  const raw = localStorage.getItem(KEY)
  return raw ? JSON.parse(raw) : null
}

export function setSession(data: any) {
  localStorage.setItem(KEY, JSON.stringify(data))
}

export function clearSession() {
  localStorage.removeItem(KEY)
}

export function getToken() {
  return getSession()?.access_token || ''
}
