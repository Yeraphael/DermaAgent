<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import BrandMark from './components/BrandMark.vue'
import { logoutUser } from './services/auth'
import { getSession } from './services/session'

const route = useRoute()
const showChrome = computed(() => route.name !== 'login')
const session = ref(getSession())

const navItems = [
  { to: '/', label: '\u9996\u9875' },
  { to: '/consultation', label: '\u667a\u80fd\u95ee\u8bca' },
  { to: '/analysis', label: '\u667a\u80fd\u5206\u6790' },
  { to: '/qa', label: '\u77e5\u8bc6\u95ee\u7b54' },
  { to: '/history', label: '\u5386\u53f2\u8bb0\u5f55' },
  { to: '/health', label: '\u5065\u5eb7\u6863\u6848' },
]

const logoutLabel = '\u9000\u51fa'
const fallbackUserName = '\u7528\u6237'
const fallbackSkinType = '\u672a\u5b8c\u5584\u6863\u6848'

function logout() {
  logoutUser()
  window.location.hash = '#/login'
}

const userDisplay = computed(() => {
  const current = session.value
  const name = current?.profile?.real_name || current?.account?.username || fallbackUserName
  const skinType = current?.health_profile?.skin_type || fallbackSkinType

  return {
    name,
    avatar: name.slice(0, 1).toUpperCase(),
    skinType,
  }
})

watch(
  () => route.fullPath,
  () => {
    session.value = getSession()
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
          <span class="portal-user__avatar">{{ userDisplay.avatar }}</span>
          <div>
            <strong>{{ userDisplay.name }}</strong>
            <span>{{ userDisplay.skinType }}</span>
          </div>
        </div>
        <button type="button" class="ghost-button" @click="logout">{{ logoutLabel }}</button>
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
