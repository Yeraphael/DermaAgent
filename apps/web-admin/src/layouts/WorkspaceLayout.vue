<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute, RouterLink, RouterView } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const doctorNav = [
  { label: '工作台', to: '/doctor/workbench' },
  { label: '问诊管理', to: '/doctor/consultations' },
  { label: '患者管理', to: '/doctor/patients' },
]

const adminNav = [
  { label: '工作台', to: '/admin/dashboard' },
  { label: '用户管理', to: '/admin/users' },
  { label: '医生管理', to: '/admin/doctors' },
  { label: '知识库管理', to: '/admin/knowledge' },
  { label: '系统配置', to: '/admin/settings' },
  { label: '日志统计', to: '/admin/logs' },
  { label: '公告管理', to: '/admin/announcements' },
]

const navItems = computed(() => (auth.role === 'DOCTOR' ? doctorNav : adminNav))
const currentTitle = computed(() => (route.meta.title as string) || '工作台')
const currentSubtitle = computed(() => (route.meta.subtitle as string) || '让设计系统和业务视图保持统一。')

function logout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="workspace-shell">
    <aside class="workspace-sidebar">
      <BrandMark />
      <nav class="workspace-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="workspace-nav__item"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="workspace-sidebar__assistant">
        <div class="workspace-sidebar__assistant-badge">AI 引擎运行中</div>
        <strong>知识增强 · 风险预警 · 安全合规</strong>
        <p>这一套后台页现在共用同一组卡片、徽标、阴影和交互节奏。</p>
      </div>
    </aside>

    <div class="workspace-main">
      <header class="workspace-topbar">
        <div>
          <p class="workspace-topbar__eyebrow">{{ auth.role === 'DOCTOR' ? '医生工作空间' : '管理运营中台' }}</p>
          <h1>{{ currentTitle }}</h1>
          <p>{{ currentSubtitle }}</p>
        </div>
        <div class="workspace-topbar__actions">
          <div class="workspace-topbar__search">
            <input type="text" placeholder="搜索菜单、病例号、知识文档…" />
          </div>
          <div class="workspace-topbar__profile">
            <img :src="auth.avatar" alt="avatar" />
            <div>
              <strong>{{ auth.account?.display_name }}</strong>
              <span>{{ auth.account?.title }}</span>
            </div>
          </div>
          <button type="button" class="ghost-button" @click="logout">退出</button>
        </div>
      </header>

      <main class="workspace-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
