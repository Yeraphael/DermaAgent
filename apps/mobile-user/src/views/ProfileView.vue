<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '../services/api'
import { clearSession } from '../services/session'

const router = useRouter()
const profile = ref<any>(null)
const notifications = ref<any[]>([])

async function loadData() {
  profile.value = await request('/user/profile')
  const notice = await request<any>('/user/notifications?page=1&page_size=5')
  notifications.value = notice.list
}

function logout() {
  clearSession()
  router.replace('/login')
}

onMounted(loadData)
</script>

<template>
  <section class="screen">
    <div class="screen-head">
      <h1 class="screen-title">{{ profile?.profile?.real_name || '皮肤健康用户' }}</h1>
      <p class="screen-subtitle">{{ profile?.account?.username }} · {{ profile?.profile?.city || '未填写城市' }}</p>
    </div>

    <div class="card">
      <div class="grid-2">
        <div class="stat-box">
          <div class="stat-label">肤质</div>
          <div class="stat-value" style="font-size: 22px;">{{ profile?.health_profile?.skin_type || '未填' }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">敏感程度</div>
          <div class="stat-value" style="font-size: 22px;">{{ profile?.health_profile?.skin_sensitivity || '未填' }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="grid-2">
        <button class="btn btn-secondary" @click="router.push('/health')">健康档案</button>
        <button class="btn btn-secondary" @click="router.push('/history')">全部记录</button>
      </div>
      <button class="btn btn-danger" style="width: 100%; margin-top: 14px;" @click="logout">退出登录</button>
    </div>

    <div class="card">
      <div class="list-title">近期通知</div>
      <div class="list" style="margin-top: 12px;">
        <article v-for="item in notifications" :key="item.notification_id" class="list-item">
          <div class="list-title">{{ item.title }}</div>
          <div class="list-meta">{{ item.content }}</div>
        </article>
      </div>
    </div>
  </section>
</template>

