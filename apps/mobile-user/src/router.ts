import { createRouter, createWebHashHistory } from 'vue-router'

import { getSession } from './services/session'
import AnalysisView from './views/AnalysisView.vue'
import ConsultationView from './views/ConsultationView.vue'
import HealthView from './views/HealthView.vue'
import HistoryView from './views/HistoryView.vue'
import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import ProfileView from './views/ProfileView.vue'
import QAView from './views/QAView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'home', component: HomeView },
    { path: '/consultation', name: 'consultation', component: ConsultationView },
    { path: '/analysis/:caseId', name: 'analysis', component: AnalysisView, props: true },
    { path: '/qa', name: 'qa', component: QAView },
    { path: '/history', name: 'history', component: HistoryView },
    { path: '/profile', name: 'profile', component: ProfileView },
    { path: '/health', name: 'health', component: HealthView },
  ],
})

router.beforeEach((to) => {
  const session = getSession()
  if (to.name !== 'login' && !session?.access_token) {
    return '/login'
  }
  if (to.name === 'login' && session?.access_token) {
    return '/'
  }
  return true
})

export default router
