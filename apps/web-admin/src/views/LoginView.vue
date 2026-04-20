<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import BrandMark from '@/components/BrandMark.vue'
import MetricCard from '@/components/MetricCard.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const form = reactive({
  username: 'doctor01',
  password: '12345678',
})

const presets = [
  {
    label: '医生端体验',
    username: 'doctor01',
    password: '12345678',
    copy: '进入高保真医生工作台，查看待处理问诊、AI 结果与回复面板。',
  },
  {
    label: '管理员体验',
    username: 'admin01',
    password: '12345678',
    copy: '进入运营中台，管理用户、医生、知识库和系统配置。',
  },
]

async function handleLogin() {
  try {
    loading.value = true
    const data = await auth.login(form.username, form.password)
    ElMessage.success('登录成功，正在进入工作空间。')
    router.push(data.account.role_type === 'ADMIN' ? '/admin/dashboard' : '/doctor/workbench')
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
  <div class="login-shell">
    <div class="login-surface">
      <section class="login-hero">
        <BrandMark />
        <div class="eyebrow-pill" style="margin-top: 26px;">AI 医疗科技感 · 统一设计系统</div>
        <h1>把医生协作、AI 辅助分析与后台治理放进同一套轻盈高级的工作台。</h1>
        <p>
          这次重构后的后台不再是传统深色表格堆砌，而是以设计图为基准，统一成白底、冰川蓝、浅紫和青绿点缀的高保真医疗科技风。
          医生端强调高效处理与清晰决策，管理端强调数据运营和秩序感。
        </p>

        <div class="login-hero__grid">
          <MetricCard label="医生端" value="3 核心工作流" note="工作台 / 问诊管理 / 患者档案" accent="violet" />
          <MetricCard label="管理端" value="7 运营模块" note="用户、医生、知识库、配置、日志与公告" accent="sky" />
          <MetricCard label="视觉系统" value="1 套统一 tokens" note="阴影、圆角、状态色、卡片与表单全量统一" accent="mint" />
        </div>
      </section>

      <section class="login-panel">
        <p class="workspace-topbar__eyebrow">DermaAgent Control Center</p>
        <h2>进入工作台</h2>
        <p>使用演示账号即可进入医生端或管理端，直接查看重构后的完整业务界面。</p>

        <form class="form-stack" @submit.prevent="handleLogin">
          <div class="form-field">
            <label for="username">账号</label>
            <input id="username" v-model="form.username" class="ghost-input" placeholder="请输入账号" />
          </div>
          <div class="form-field">
            <label for="password">密码</label>
            <input id="password" v-model="form.password" class="ghost-input" type="password" placeholder="请输入密码" />
          </div>
          <button type="submit" class="primary-button" :disabled="loading">
            {{ loading ? '正在进入…' : '进入工作空间' }}
          </button>
        </form>

        <div class="preset-grid">
          <button
            v-for="item in presets"
            :key="item.label"
            type="button"
            class="preset-button"
            @click="usePreset(item.username, item.password)"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.username }} / {{ item.password }}</span>
          </button>
        </div>

        <p class="helper-copy" style="margin-top: 18px;">
          演示说明：
          <span class="accent-text">当前登录流程为可运行的本地 mock 数据驱动</span>，
          后续可平滑接回真实接口层而不影响本套页面结构。
        </p>
      </section>
    </div>
  </div>
</template>
