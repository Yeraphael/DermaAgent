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
  username: '',
  password: '',
})

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
</script>

<template>
  <div class="login-shell">
    <div class="login-surface">
      <section class="login-hero">
        <BrandMark />
        <div class="eyebrow-pill" style="margin-top: 26px;">统一医疗运营工作空间</div>
        <h1>把医生协作、平台治理和 AI 辅助分析放进同一套正式可用的后台。</h1>
        <p>
          医生端围绕问诊处理、患者档案和 AI 复核展开，管理端围绕账号治理、咨询监管、系统配置和日志监控展开。
          整体采用与用户端一致的浅色医疗科技风格，保证信息层级清晰、操作路径连贯。
        </p>

        <div class="login-hero__grid">
          <MetricCard label="医生端" value="工作台 / 问诊 / 档案" note="围绕处理效率、风险判断与连续随访。" accent="violet" />
          <MetricCard label="管理端" value="控制台 / 运营治理" note="覆盖用户、医生、咨询、配置和日志。" accent="sky" />
          <MetricCard label="数据闭环" value="用户端联动" note="问诊提交、医生回复和 AI 反馈实时回写。" accent="mint" />
        </div>
      </section>

      <section class="login-panel">
        <p class="workspace-topbar__eyebrow">DermaAgent Workspace</p>
        <h2>账号登录</h2>
        <p>请输入已开通的医生或管理员账号信息，系统会根据角色自动进入对应工作空间。</p>

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

        <div class="login-panel__tips">
          <div class="detail-card">
            <div class="tiny-label">登录后可用能力</div>
            <p class="detail-copy">医生可处理待办问诊、查看患者长期档案并提交专业回复；管理员可管理账号、审核医生、监管咨询流程与系统参数。</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
