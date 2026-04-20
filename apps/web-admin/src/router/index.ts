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
            subtitle: '高风险预警、待处理问诊、AI 反馈准确率和效率趋势都收敛到同一套设计语言里。',
          },
        },
        {
          path: 'consultations/:id?',
          component: DoctorConsultationsView,
          meta: {
            title: '问诊管理',
            subtitle: '左侧列表、中间详情、右侧回复与反馈面板，对齐设计图中的专业轻盈三栏结构。',
          },
        },
        {
          path: 'patients',
          component: DoctorPatientsView,
          meta: {
            title: '患者管理',
            subtitle: '把健康档案、生活习惯、过敏史和历史病例放进统一的产品化档案视图。',
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
            subtitle: '统一展示关键经营指标、知识库流程、趋势曲线和运营日志，保持高级秩序感。',
          },
        },
        {
          path: 'users',
          component: AdminUsersView,
          meta: {
            title: '用户管理',
            subtitle: '用户画像、风险偏好与状态操作被重构成精致轻盈的管理列表。',
          },
        },
        {
          path: 'doctors',
          component: AdminDoctorsView,
          meta: {
            title: '医生管理',
            subtitle: '审核、启停和擅长方向聚合展示，强调中台产品感而非传统后台表格感。',
          },
        },
        {
          path: 'knowledge',
          component: AdminKnowledgeView,
          meta: {
            title: '知识库管理',
            subtitle: '上传、解析、切片、向量化和可检索全流程可视化，让 RAG 底座更易展示与管理。',
          },
        },
        {
          path: 'settings',
          component: AdminSettingsView,
          meta: {
            title: '系统配置',
            subtitle: 'Prompt 模板版本、医生复核开关、上传限制和提醒窗口在同一设计系统下统一编辑。',
          },
        },
        {
          path: 'logs',
          component: AdminLogsView,
          meta: {
            title: '日志统计',
            subtitle: '操作日志与模型调用日志拆分展示，方便治理、回溯与性能观察。',
          },
        },
        {
          path: 'announcements',
          component: AdminAnnouncementsView,
          meta: {
            title: '公告管理',
            subtitle: '面向医生和用户的公告发布入口被做成更适合答辩演示的产品化模块。',
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
