<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import BrandMark from './components/BrandMark.vue'
import { clearPortalSession, getPortalSession } from './shared/portal'

const route = useRoute()
const showChrome = computed(() => route.name !== 'login')
const session = ref(getPortalSession())

const navItems = [
  { to: '/', label: '首页' },
  { to: '/consultation', label: '智能问诊' },
  { to: '/analysis', label: 'AI 分析' },
  { to: '/qa', label: '知识问答' },
  { to: '/history', label: '历史记录' },
  { to: '/health', label: '健康档案' },
]

function logout() {
  clearPortalSession()
  window.location.hash = '#/login'
}

watch(
  () => route.fullPath,
  () => {
    session.value = getPortalSession()
  },
  { immediate: true },
)
</script>

<template>
  <div class="portal-app">
    <div class="portal-bg portal-bg--left" />
    <div class="portal-bg portal-bg--right" />
    <div class="portal-bg portal-bg--bottom" />

    <header v-if="showChrome" class="portal-header">
      <BrandMark />
      <nav class="portal-nav">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="portal-nav__item">
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="portal-header__actions">
        <div class="portal-user">
          <span class="portal-user__avatar">{{ session?.profile.real_name.slice(0, 1) }}</span>
          <div>
            <strong>{{ session?.profile.real_name }}</strong>
            <span>{{ session?.profile.skin_type }}</span>
          </div>
        </div>
        <button type="button" class="ghost-button" @click="logout">退出</button>
      </div>
    </header>

    <main class="portal-stage" :class="{ 'portal-stage--login': !showChrome }">
      <RouterView />
    </main>

    <nav v-if="showChrome" class="portal-dock">
      <RouterLink v-for="item in navItems.slice(0, 5)" :key="item.to" :to="item.to" class="portal-dock__item">
        {{ item.label }}
      </RouterLink>
    </nav>
  </div>
</template>
