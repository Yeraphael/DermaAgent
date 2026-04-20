import { getPortalSession } from '../shared/portal'

export type MiniTabKey = 'home' | 'consultation' | 'qa' | 'history' | 'profile'

const tabRoutes: Record<MiniTabKey, string> = {
  home: '/pages/home/index',
  consultation: '/pages/consultation/index',
  qa: '/pages/qa/index',
  history: '/pages/history/index',
  profile: '/pages/profile/index',
}

export function ensurePortalLogin() {
  if (!getPortalSession()?.access_token) {
    uni.reLaunch({ url: '/pages/login/index' })
    return false
  }
  return true
}

export function openMiniTab(key: MiniTabKey) {
  uni.reLaunch({ url: tabRoutes[key] })
}

export function openMiniPage(url: string) {
  uni.navigateTo({ url })
}
