import { createRouter, createWebHistory } from 'vue-router'

import WorkspaceLayout from '@/layouts/WorkspaceLayout.vue'
import { useAuthStore } from '@/stores/auth'
import AdminAnnouncementsView from '@/views/admin/AdminAnnouncementsView.vue'
import AdminDashboardView from '@/views/admin/AdminDashboardView.vue'
import AdminDoctorsView from '@/views/admin/AdminDoctorsView.vue'
import AdminKnowledgeView from '@/views/admin/AdminKnowledgeView.vue'
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
            title: '医生工作台',
            subtitle: '高风险预警、待处理问诊、AI 反馈准确率和效率趋势都收敛到同一套清晰的工作视图里。',
          },
        },
        {
          path: 'consultations/:id?',
          component: DoctorConsultationsView,
          meta: {
            title: '问诊管理',
            subtitle: '左侧病例列表、中间问诊详情、右侧医生回复与 AI 反馈保持统一的三栏协作结构。',
          },
        },
        {
          path: 'patients',
          component: DoctorPatientsView,
          meta: {
            title: '患者管理',
            subtitle: '把健康档案、过敏史、生活习惯和历史病例整合到同一套可持续跟踪的患者视图里。',
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
            title: '控制台 / 数据看板',
            subtitle: '统一展示核心运营指标、知识库流程、趋势曲线和运行日志，保持轻盈但专业的中台质感。',
          },
        },
        {
          path: 'users',
          component: AdminUsersView,
          meta: {
            title: '用户管理',
            subtitle: '用统一的大字号和高对比视图管理用户状态、画像标签和最近问诊情况。',
          },
        },
        {
          path: 'doctors',
          component: AdminDoctorsView,
          meta: {
            title: '医生管理',
            subtitle: '审核、启停和擅长方向集中展示，弱化传统后台表格感，强化产品化管理体验。',
          },
        },
        {
          path: 'knowledge',
          component: AdminKnowledgeView,
          meta: {
            title: '知识库管理',
            subtitle: '上传、解析、切片、向量化和可检索状态统一可视化，方便演示和日常维护。',
          },
        },
        {
          path: 'settings',
          component: AdminSettingsView,
          meta: {
            title: '系统配置',
            subtitle: 'Prompt 版本、医生复核开关、上传限制和提醒窗口在同一设计语言下统一编辑。',
          },
        },
        {
          path: 'logs',
          component: AdminLogsView,
          meta: {
            title: '日志统计',
            subtitle: '操作日志与模型调用日志分层展示，便于治理、回溯和性能观察。',
          },
        },
        {
          path: 'announcements',
          component: AdminAnnouncementsView,
          meta: {
            title: '公告管理',
            subtitle: '面向医生和用户的公告入口统一收口，兼顾答辩展示与后续维护体验。',
          },
        },
      ],
    },
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
    return auth.role === 'ADMIN' ? '/admin/dashboard' : '/login'
  }
  if (to.path.startsWith('/admin') && auth.role !== 'ADMIN') {
    return auth.role === 'DOCTOR' ? '/doctor/workbench' : '/login'
  }
  return true
})

export default router
