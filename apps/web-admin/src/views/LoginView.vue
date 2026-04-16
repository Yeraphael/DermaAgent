<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({
  username: 'doctor01',
  password: '12345678',
})

const presets = [
  { label: '医生端体验', username: 'doctor01', password: '12345678' },
  { label: '管理员体验', username: 'admin01', password: '12345678' },
]

async function handleLogin() {
  try {
    loading.value = true
    const data = await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push(data.account.role_type === 'ADMIN' ? '/admin' : '/doctor')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

function usePreset(username: string, password: string) {
  form.username = username
  form.password = password
}
</script>

<template>
  <div class="page-shell" style="display: grid; place-items: center;">
    <div
      class="glass-panel"
      style="
        width: min(1120px, 100%);
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        overflow: hidden;
      "
    >
      <section style="padding: 40px; border-right: 1px solid rgba(181, 216, 255, 0.08);">
        <div style="display: inline-flex; align-items: center; gap: 10px; padding: 8px 14px; border-radius: 999px; background: rgba(89, 228, 194, 0.14); color: #c8fff2;">
          肤联智诊 · 智慧皮肤健康协同平台
        </div>
        <h1 style="margin: 26px 0 14px; font-size: 42px; line-height: 1.16;">
          让 AI 辅助分析、医生复核与平台治理在一套系统中闭环协同
        </h1>
        <p style="margin: 0; color: var(--text-sub); font-size: 16px; line-height: 1.8;">
          管理台支持医生查看待处理问诊、参考 AI 图文分析给出专业建议，也支持管理员完成用户管理、医生审核、知识库维护与运行统计。
        </p>

        <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 32px;">
          <div class="stat-card">
            <span class="stat-label">AI 图文分析</span>
            <strong>图像 + 症状</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">医生协同</span>
            <strong>问诊闭环</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">运营治理</span>
            <strong>日志统计</strong>
          </div>
        </div>
      </section>

      <section style="padding: 36px;">
        <div style="margin-bottom: 24px;">
          <h2 style="margin: 0; font-size: 28px;">工作台登录</h2>
          <p style="margin: 8px 0 0; color: var(--text-sub);">选择医生或管理员账号进入对应业务空间。</p>
        </div>

        <el-form label-position="top" @submit.prevent="handleLogin">
          <el-form-item label="账号">
            <el-input v-model="form.username" size="large" placeholder="请输入账号" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" size="large" type="password" show-password placeholder="请输入密码" />
          </el-form-item>
          <el-button class="accent-button" type="primary" size="large" :loading="loading" style="width: 100%;" @click="handleLogin">
            进入工作台
          </el-button>
        </el-form>

        <div style="margin-top: 26px;">
          <div style="margin-bottom: 12px; color: var(--text-sub);">快捷测试账号</div>
          <div style="display: flex; flex-wrap: wrap; gap: 12px;">
            <button
              v-for="item in presets"
              :key="item.label"
              type="button"
              style="
                cursor: pointer;
                border: 1px solid rgba(181, 216, 255, 0.12);
                color: var(--text-main);
                background: rgba(11, 25, 42, 0.72);
                border-radius: 16px;
                padding: 12px 16px;
              "
              @click="usePreset(item.username, item.password)"
            >
              {{ item.label }} · {{ item.username }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
