import { createRouter, createWebHashHistory } from 'vue-router'

import { getSession } from './services/session'
import AnalysisView from './views/AnalysisView.vue'
import ConsultationView from './views/ConsultationView.vue'
import HealthView from './views/HealthView.vue'
import HistoryView from './views/HistoryView.vue'
import LoginView from './views/LoginView.vue'
import ProfileView from './views/ProfileView.vue'
import QAView from './views/QAView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', redirect: '/consultation' },
    { path: '/consultation', name: 'consultation', component: ConsultationView },
    { path: '/analysis/:caseId?', name: 'analysis', component: AnalysisView, props: true },
    { path: '/qa', name: 'qa', component: QAView },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/health', name: 'health', component: HealthView },
    { path: '/profile', name: 'profile', component: ProfileView },
  ],
})

router.beforeEach((to) => {
  const session = getSession()
  if (to.name !== 'login' && !session?.access_token) {
    return '/login'
  }
  if (to.name === 'login' && session?.access_token) {
    return '/consultation'
  }
  return true
})

export default router
