import { createRouter, createWebHistory } from 'vue-router'

import WorkspaceLayout from '@/layouts/WorkspaceLayout.vue'
import { useAuthStore } from '@/stores/auth'
import AdminConsultationsView from '@/views/admin/AdminConsultationsView.vue'
import AdminDashboardView from '@/views/admin/AdminDashboardView.vue'
import AdminDoctorsView from '@/views/admin/AdminDoctorsView.vue'
import AdminLogsView from '@/views/admin/AdminLogsView.vue'
import AdminSettingsView from '@/views/admin/AdminSettingsView.vue'
import AdminUsersView from '@/views/admin/AdminUsersView.vue'
import DoctorConsultationsView from '@/views/doctor/DoctorConsultationsView.vue'
import DoctorPatientsView from '@/views/doctor/DoctorPatientsView.vue'
import DoctorWorkbenchView from '@/views/doctor/DoctorWorkbenchView.vue'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: LoginView },
    {
      path: '/doctor',
      component: WorkspaceLayout,
      meta: { role: 'DOCTOR' },
      children: [
        { path: '', redirect: '/doctor/workbench' },
        {
          path: 'workbench',
          component: DoctorWorkbenchView,
          meta: {
            title: '工作台',
            subtitle: '集中查看待处理问诊、高风险提醒、今日处理效率和 AI 反馈表现。',
          },
        },
        {
          path: 'consultations/:id?',
          component: DoctorConsultationsView,
          meta: {
            title: '问诊管理',
            subtitle: '查看图文问诊、患者资料、AI 分析结果，并完成医生回复与结果反馈。',
          },
        },
        {
          path: 'patients/:userId?',
          component: DoctorPatientsView,
          meta: {
            title: '患者档案',
            subtitle: '统一管理患者基础信息、健康标签、历史病例、风险趋势与长期护理建议。',
          },
        },
      ],
    },
    {
      path: '/admin',
      component: WorkspaceLayout,
      meta: { role: 'ADMIN' },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        {
          path: 'dashboard',
          component: AdminDashboardView,
          meta: {
            title: '控制台',
            subtitle: '查看平台运营指标、待审核医生、咨询趋势、重点告警和医生处理概览。',
          },
        },
        {
          path: 'users/:userId?',
          component: AdminUsersView,
          meta: {
            title: '用户管理',
            subtitle: '管理普通用户账号状态、查看健康档案与最近咨询，保障平台安全运营。',
          },
        },
        {
          path: 'doctors/:doctorId?',
          component: AdminDoctorsView,
          meta: {
            title: '医生管理',
            subtitle: '处理医生资质审核、服务状态切换、回复率统计与履约情况。',
          },
        },
        {
          path: 'consultations/:id?',
          component: AdminConsultationsView,
          meta: {
            title: '咨询记录',
            subtitle: '查看全平台问诊详情、AI 结果、医生回复、处理时间线，并支持异常标记与归档。',
          },
        },
        {
          path: 'settings',
          component: AdminSettingsView,
          meta: {
            title: '系统配置',
            subtitle: '维护模型参数、提示词模板、风险规则、上传限制、通知规则和权限配置。',
          },
        },
        {
          path: 'logs',
          component: AdminLogsView,
          meta: {
            title: '日志监控',
            subtitle: '查看登录日志、操作日志、AI 调用、异常告警和系统运行趋势。',
          },
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.path === '/login') return true

  if (!auth.token) return '/login'

  if (!auth.account) {
    try {
      await auth.loadProfile()
    } catch {
      await auth.logout()
      return '/login'
    }
  }

  if (to.path.startsWith('/doctor') && auth.role !== 'DOCTOR') {
    return auth.role === 'ADMIN' ? '/admin/dashboard' : '/login'
  }
  if (to.path.startsWith('/admin') && auth.role !== 'ADMIN') {
    return auth.role === 'DOCTOR' ? '/doctor/workbench' : '/login'
  }
  return true
})

export default router
