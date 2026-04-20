<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import BrandMark from '../components/BrandMark.vue'
import { loginPortalUser } from '../shared/portal'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')
const form = reactive({
  username: 'user01',
  password: '12345678',
})

async function login() {
  try {
    loading.value = true
    errorMessage.value = ''
    await loginPortalUser(form.username, form.password)
    router.replace('/')
  } catch (error) {
    errorMessage.value = (error as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="login-layout">
    <article class="login-hero">
      <BrandMark />
      <p class="section-eyebrow" style="margin-top: 26px;">AI 皮肤健康 · 智能随行</p>
      <h1>把图文问诊、AI 辅助分析、医生回复与知识问答放进同一个高保真入口。</h1>
      <p>
        用户端完全按照浅色、轻盈、现代的医疗科技产品气质重构，兼顾 Web/H5 展示和小程序可迁移风格。
        上传图片、提交症状、查看 AI 结果、接收医生回复和持续问答都在同一套设计语言中完成。
      </p>

      <div class="login-card-grid">
        <article>
          <span class="section-eyebrow">体验</span>
          <strong>高保真用户端</strong>
        </article>
        <article>
          <span class="section-eyebrow">业务</span>
          <strong>问诊 / AI / 问答</strong>
        </article>
        <article>
          <span class="section-eyebrow">风格</span>
          <strong>冰川蓝 · 青绿 · 浅紫</strong>
        </article>
      </div>
    </article>

    <article class="login-panel">
      <p class="section-eyebrow">DermaAgent User Portal</p>
      <h2 class="card-title" style="margin-top: 6px;">进入健康空间</h2>
      <p class="section-subtitle">使用演示账号即可体验完整的用户端问诊流程。</p>

      <div class="page-stack" style="margin-top: 24px;">
        <div class="field">
          <label>账号</label>
          <input v-model="form.username" class="ghost-input" placeholder="请输入账号" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="form.password" class="ghost-input" type="password" placeholder="请输入密码" />
        </div>
        <button type="button" class="primary-button" @click="login">
          {{ loading ? '正在进入…' : '进入我的皮肤健康空间' }}
        </button>
        <button type="button" class="ghost-button" @click="form.username = 'user01'; form.password = '12345678'">
          使用默认演示账号
        </button>
        <p v-if="errorMessage" class="card-copy" style="color: #e45e72;">{{ errorMessage }}</p>
      </div>
    </article>
  </section>
</template>
