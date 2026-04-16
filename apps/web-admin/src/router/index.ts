import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import AdminPortal from '@/views/AdminPortal.vue'
import ConsultationDetail from '@/views/ConsultationDetail.vue'
import DoctorPortal from '@/views/DoctorPortal.vue'
import LoginView from '@/views/LoginView.vue'
import PatientProfile from '@/views/PatientProfile.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: LoginView },
    { path: '/doctor', component: DoctorPortal },
    { path: '/doctor/consultations/:id', component: ConsultationDetail, props: true },
    { path: '/doctor/patients/:id', component: PatientProfile, props: true },
    { path: '/admin', component: AdminPortal },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.path === '/login') {
    return true
  }
  if (!auth.token) {
    return '/login'
  }
  if (!auth.account) {
    await auth.loadProfile()
  }
  if (to.path.startsWith('/doctor') && auth.role !== 'DOCTOR') {
    return auth.role === 'ADMIN' ? '/admin' : '/login'
  }
  if (to.path.startsWith('/admin') && auth.role !== 'ADMIN') {
    return auth.role === 'DOCTOR' ? '/doctor' : '/login'
  }
  return true
})

export default router
