<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '../services/api'
import { setSession } from '../services/session'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: 'user01',
  password: '12345678',
})
const errorMessage = ref('')

async function login() {
  try {
    loading.value = true
    errorMessage.value = ''
    const data = await request('/auth/login', {
      method: 'POST',
      data: form,
    })
    setSession(data)
    router.replace('/')
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="screen" style="padding-top: 28px;">
    <div class="card">
      <div class="pill">肤联智诊 · H5 用户端</div>
      <h1 class="hero-title">图文问诊、AI 辅助分析与医生协同，在一个入口完成。</h1>
      <p class="hero-copy">登录后即可上传皮肤图片、发起问诊、查看 AI 风险提示并继续健康问答。</p>

      <div class="field" style="margin-top: 20px;">
        <label>账号</label>
        <input v-model="form.username" class="input" placeholder="请输入账号" />
      </div>

      <div class="field" style="margin-top: 14px;">
        <label>密码</label>
        <input v-model="form.password" class="input" type="password" placeholder="请输入密码" />
      </div>

      <button class="btn btn-primary" style="width: 100%; margin-top: 18px;" :disabled="loading" @click="login">
        {{ loading ? '登录中...' : '进入健康空间' }}
      </button>

      <button class="btn btn-secondary" style="width: 100%; margin-top: 12px;" @click="form.username='user01'; form.password='12345678'">
        使用默认测试账号
      </button>

      <p v-if="errorMessage" class="notice" style="margin-top: 14px;">{{ errorMessage }}</p>
    </div>
  </section>
</template>

