<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'

import BrandMark from './components/BrandMark.vue'
import { fetchCurrentSession, logoutUser } from './services/auth'
import { getSession } from './services/session'
import { getInitial, maskPhone, sanitizeVisibleText } from './utils/display'

const route = useRoute()
const router = useRouter()

const showChrome = computed(() => route.name !== 'login')
const session = ref(getSession())
const userMenuOpen = ref(false)
const refreshingSession = ref(false)

const navItems = [
  { to: '/consultation', label: '图文问诊' },
  { to: '/analysis', label: '智能分析' },
  { to: '/qa', label: '知识问答' },
  { to: '/history', label: '历史记录' },
  { to: '/health', label: '健康档案' },
]

const userDisplay = computed(() => {
  const current = session.value
  const name = sanitizeVisibleText(current?.profile?.real_name || current?.account?.username, '健康用户')
  const skinType = sanitizeVisibleText(current?.health_profile?.skin_type, '完善皮肤信息后可获得更准确建议')

  return {
    name,
    phone: maskPhone(current?.account?.phone),
    skinType,
    avatarText: getInitial(name),
  }
})

async function syncSession() {
  const current = getSession()
  if (!current?.access_token || refreshingSession.value) {
    session.value = current
    return
  }

  try {
    refreshingSession.value = true
    await fetchCurrentSession()
  } catch {
    // Ignore refresh failures and continue to use local session.
  } finally {
    session.value = getSession()
    refreshingSession.value = false
  }
}

function closeMenu() {
  userMenuOpen.value = false
}

function toggleMenu() {
  userMenuOpen.value = !userMenuOpen.value
}

function handleBodyClick(event: MouseEvent) {
  const target = event.target as HTMLElement | null
  if (!target?.closest('.portal-user-menu')) {
    closeMenu()
  }
}

function goProfile() {
  closeMenu()
  router.push('/profile')
}

function showPlaceholder(title: string) {
  closeMenu()
  window.alert(`${title}正在完善中，敬请期待。`)
}

async function handleLogout() {
  closeMenu()
  const confirmed = window.confirm('确认退出登录？\n退出后需要重新登录。')
  if (!confirmed) {
    return
  }

  await logoutUser()
  router.replace('/login')
}

watch(
  () => route.fullPath,
  () => {
    session.value = getSession()
    closeMenu()
  },
  { immediate: true },
)

onMounted(() => {
  void syncSession()
  window.addEventListener('click', handleBodyClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleBodyClick)
})
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

      <div class="portal-user-menu">
        <button type="button" class="portal-user-trigger" @click.stop="toggleMenu">
          <span class="portal-user__avatar">{{ userDisplay.avatarText }}</span>
          <span class="portal-user__meta">
            <strong>{{ userDisplay.name }}</strong>
            <span>{{ userDisplay.skinType }}</span>
          </span>
          <span class="portal-user-trigger__arrow" :class="{ 'is-open': userMenuOpen }">⌄</span>
        </button>

        <div v-if="userMenuOpen" class="portal-user-dropdown">
          <div class="portal-user-dropdown__summary">
            <strong>{{ userDisplay.name }}</strong>
            <span>{{ userDisplay.phone || '已登录' }}</span>
          </div>
          <button type="button" class="portal-menu-item" @click="goProfile">个人资料</button>
          <button type="button" class="portal-menu-item" @click="showPlaceholder('我的消息')">我的消息</button>
          <button type="button" class="portal-menu-item" @click="showPlaceholder('帮助中心')">帮助中心</button>
          <button type="button" class="portal-menu-item" @click="showPlaceholder('关于我们')">关于我们</button>
          <button type="button" class="portal-menu-item portal-menu-item--danger" @click="handleLogout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="portal-stage" :class="{ 'portal-stage--login': !showChrome }">
      <RouterView />
    </main>

    <nav v-if="showChrome" class="portal-dock">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="portal-dock__item">
        {{ item.label }}
      </RouterLink>
    </nav>
  </div>
</template>
