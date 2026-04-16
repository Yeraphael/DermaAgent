<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
const showTabbar = computed(() => route.name !== 'login')

const tabs = [
  { to: '/', label: '首页' },
  { to: '/consultation', label: '问诊' },
  { to: '/qa', label: '问答' },
  { to: '/history', label: '记录' },
  { to: '/profile', label: '我的' },
]
</script>

<template>
  <div class="mobile-app">
    <div class="bg-orb bg-orb-left"></div>
    <div class="bg-orb bg-orb-right"></div>
    <main class="mobile-stage">
      <RouterView />
    </main>

    <nav v-if="showTabbar" class="mobile-tabbar">
      <RouterLink v-for="item in tabs" :key="item.to" :to="item.to" class="mobile-tab">
        {{ item.label }}
      </RouterLink>
    </nav>
  </div>
</template>
