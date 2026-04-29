<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import BrandMark from '../components/BrandMark.vue'
import { loginUser, registerUser, resetPassword, sendVerificationCode } from '../services/auth'

type AuthMode = 'login' | 'register' | 'reset'

const router = useRouter()

const activeMode = ref<AuthMode>('login')
const loading = ref(false)
const codeSending = ref(false)
const cooldown = ref(0)
const feedback = ref('')
let countdownTimer: number | undefined

const loginForm = reactive({
  phone: '',
  password: '',
})

const registerForm = reactive({
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
})

const resetForm = reactive({
  phone: '',
  code: '',
  password: '',
  confirmPassword: '',
})

const pageTitle = computed(() => {
  if (activeMode.value === 'register') return '创建账号'
  if (activeMode.value === 'reset') return '找回密码'
  return '登录'
})

const pageSubtitle = computed(() => {
  if (activeMode.value === 'register') return '填写手机号与验证码，快速完成注册。'
  if (activeMode.value === 'reset') return '通过验证码重置密码，重新登录您的账户。'
  return '请输入手机号和密码，继续使用肤联智诊。'
})

function setMode(mode: AuthMode) {
  activeMode.value = mode
  feedback.value = ''
}

function isValidPhone(phone: string) {
  return /^1\d{10}$/.test(phone.trim())
}

function startCooldown(seconds = 60) {
  cooldown.value = seconds
  window.clearInterval(countdownTimer)
  countdownTimer = window.setInterval(() => {
    cooldown.value = Math.max(0, cooldown.value - 1)
    if (cooldown.value === 0) {
      window.clearInterval(countdownTimer)
    }
  }, 1000)
}

async function handleSendCode(scene: 'REGISTER' | 'RESET_PASSWORD') {
  const phone = scene === 'REGISTER' ? registerForm.phone.trim() : resetForm.phone.trim()
  if (!isValidPhone(phone)) {
    feedback.value = '请输入正确的手机号后再获取验证码。'
    return
  }

  try {
    codeSending.value = true
    feedback.value = ''
    const response = await sendVerificationCode(phone, scene)
    startCooldown(Math.min(response.expires_in || 60, 60))
    window.alert('验证码请求已提交，请注意查收。')
  } catch (error) {
    feedback.value = (error as Error).message || '验证码发送失败，请稍后重试。'
  } finally {
    codeSending.value = false
  }
}

async function submitLogin() {
  if (!isValidPhone(loginForm.phone)) {
    feedback.value = '请输入正确的手机号。'
    return
  }
  if (!loginForm.password.trim()) {
    feedback.value = '请输入密码。'
    return
  }

  try {
    loading.value = true
    feedback.value = ''
    await loginUser(loginForm.phone.trim(), loginForm.password)
    router.replace('/consultation')
  } catch (error) {
    feedback.value = (error as Error).message || '登录失败，请检查手机号和密码。'
  } finally {
    loading.value = false
  }
}

async function submitRegister() {
  if (!isValidPhone(registerForm.phone)) {
    feedback.value = '请输入正确的手机号。'
    return
  }
  if (!registerForm.code.trim()) {
    feedback.value = '请输入验证码。'
    return
  }
  if (registerForm.password.length < 6) {
    feedback.value = '密码长度不少于 6 位。'
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    feedback.value = '两次输入的密码不一致。'
    return
  }

  try {
    loading.value = true
    feedback.value = ''
    await registerUser({
      phone: registerForm.phone.trim(),
      code: registerForm.code.trim(),
      password: registerForm.password,
    })
    await loginUser(registerForm.phone.trim(), registerForm.password)
    router.replace('/consultation')
  } catch (error) {
    feedback.value = (error as Error).message || '注册失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function submitReset() {
  if (!isValidPhone(resetForm.phone)) {
    feedback.value = '请输入正确的手机号。'
    return
  }
  if (!resetForm.code.trim()) {
    feedback.value = '请输入验证码。'
    return
  }
  if (resetForm.password.length < 6) {
    feedback.value = '新密码长度不少于 6 位。'
    return
  }
  if (resetForm.password !== resetForm.confirmPassword) {
    feedback.value = '两次输入的新密码不一致。'
    return
  }

  try {
    loading.value = true
    feedback.value = ''
    await resetPassword({
      phone: resetForm.phone.trim(),
      code: resetForm.code.trim(),
      password: resetForm.password,
    })
    loginForm.phone = resetForm.phone.trim()
    loginForm.password = ''
    setMode('login')
    window.alert('密码修改成功，请使用新密码登录。')
  } catch (error) {
    feedback.value = (error as Error).message || '密码重置失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (activeMode.value === 'register') {
    await submitRegister()
    return
  }
  if (activeMode.value === 'reset') {
    await submitReset()
    return
  }
  await submitLogin()
}

onBeforeUnmount(() => {
  window.clearInterval(countdownTimer)
})
</script>

<template>
  <section class="auth-layout">
    <article class="auth-hero">
      <BrandMark />
      <p class="section-eyebrow auth-hero__eyebrow">智能问诊 · 皮肤健康管理</p>
      <h1>肤联智诊</h1>
      <p class="auth-hero__copy">
        上传皮肤图片，补充症状信息，查看智能分析结果，并持续接收医生回复和护理建议。
      </p>

      <div class="auth-tag-row">
        <span>安全问诊</span>
        <span>专业建议</span>
        <span>隐私保护</span>
      </div>

      <div class="auth-feature-list">
        <article>
          <strong>图文问诊</strong>
          <p>围绕皮肤症状上传图片并补充症状细节，快速发起线上问诊。</p>
        </article>
        <article>
          <strong>智能分析</strong>
          <p>结合图片和症状信息输出病例摘要、护理建议与风险提醒。</p>
        </article>
        <article>
          <strong>持续跟踪</strong>
          <p>历史记录、健康档案和知识问答同步沉淀，便于长期观察皮肤变化。</p>
        </article>
      </div>
    </article>

    <article class="auth-panel">
      <div class="auth-tabs">
        <button type="button" :class="{ 'is-active': activeMode === 'login' }" @click="setMode('login')">登录</button>
        <button type="button" :class="{ 'is-active': activeMode === 'register' }" @click="setMode('register')">注册</button>
      </div>

      <div class="auth-panel__head">
        <h2 class="card-title">{{ pageTitle }}</h2>
        <p class="section-subtitle">{{ pageSubtitle }}</p>
      </div>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <template v-if="activeMode === 'login'">
          <div class="field">
            <label>手机号</label>
            <input v-model="loginForm.phone" class="ghost-input" inputmode="numeric" maxlength="11" placeholder="请输入手机号" />
          </div>

          <div class="field">
            <label>密码</label>
            <input v-model="loginForm.password" class="ghost-input" type="password" placeholder="请输入密码" />
          </div>

          <div class="auth-links">
            <button type="button" class="text-button" @click="setMode('reset')">忘记密码</button>
            <button type="button" class="text-button" @click="setMode('register')">立即注册</button>
          </div>
        </template>

        <template v-else-if="activeMode === 'register'">
          <div class="field">
            <label>手机号</label>
            <input v-model="registerForm.phone" class="ghost-input" inputmode="numeric" maxlength="11" placeholder="请输入手机号" />
          </div>

          <div class="field">
            <label>验证码</label>
            <div class="field-with-action">
              <input v-model="registerForm.code" class="ghost-input" inputmode="numeric" maxlength="6" placeholder="请输入验证码" />
              <button
                type="button"
                class="secondary-button field-with-action__button"
                :disabled="codeSending || cooldown > 0"
                @click="handleSendCode('REGISTER')"
              >
                {{ cooldown > 0 ? `${cooldown}s 后重试` : '获取验证码' }}
              </button>
            </div>
          </div>

          <div class="field">
            <label>密码</label>
            <input v-model="registerForm.password" class="ghost-input" type="password" placeholder="请输入密码" />
          </div>

          <div class="field">
            <label>确认密码</label>
            <input v-model="registerForm.confirmPassword" class="ghost-input" type="password" placeholder="请再次输入密码" />
          </div>

          <div class="auth-links auth-links--single">
            <button type="button" class="text-button" @click="setMode('login')">已有账号？去登录</button>
          </div>
        </template>

        <template v-else>
          <div class="field">
            <label>手机号</label>
            <input v-model="resetForm.phone" class="ghost-input" inputmode="numeric" maxlength="11" placeholder="请输入手机号" />
          </div>

          <div class="field">
            <label>验证码</label>
            <div class="field-with-action">
              <input v-model="resetForm.code" class="ghost-input" inputmode="numeric" maxlength="6" placeholder="请输入验证码" />
              <button
                type="button"
                class="secondary-button field-with-action__button"
                :disabled="codeSending || cooldown > 0"
                @click="handleSendCode('RESET_PASSWORD')"
              >
                {{ cooldown > 0 ? `${cooldown}s 后重试` : '获取验证码' }}
              </button>
            </div>
          </div>

          <div class="field">
            <label>新密码</label>
            <input v-model="resetForm.password" class="ghost-input" type="password" placeholder="请输入新密码" />
          </div>

          <div class="field">
            <label>确认新密码</label>
            <input v-model="resetForm.confirmPassword" class="ghost-input" type="password" placeholder="请再次输入新密码" />
          </div>

          <div class="auth-links auth-links--single">
            <button type="button" class="text-button" @click="setMode('login')">返回登录</button>
          </div>
        </template>

        <p v-if="feedback" class="auth-feedback">{{ feedback }}</p>

        <button type="submit" class="primary-button auth-submit" :disabled="loading">
          {{ loading ? '提交中...' : activeMode === 'register' ? '创建账号' : activeMode === 'reset' ? '确认修改' : '登录' }}
        </button>
      </form>
    </article>
  </section>
</template>

<style scoped>
.auth-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 18px;
}

.auth-hero,
.auth-panel {
  padding: 32px;
}

.auth-hero {
  display: grid;
  align-content: space-between;
  gap: 24px;
  min-height: 680px;
  background:
    radial-gradient(circle at 0% 0%, rgba(209, 232, 255, 0.78), transparent 28%),
    radial-gradient(circle at 90% 100%, rgba(213, 207, 255, 0.52), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 249, 255, 0.96) 100%);
}

.auth-hero__eyebrow {
  margin: 0;
}

.auth-hero h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 42px;
  line-height: 1.12;
}

.auth-hero__copy {
  margin: 0;
  max-width: 520px;
  color: var(--text-sub);
  font-size: 15px;
  line-height: 1.9;
}

.auth-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.auth-tag-row span {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(47, 125, 255, 0.08);
  color: var(--blue);
  font-size: 13px;
  font-weight: 700;
}

.auth-feature-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.auth-feature-list article {
  padding: 18px;
  border: 1px solid rgba(168, 188, 224, 0.3);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
}

.auth-feature-list strong {
  display: block;
  color: var(--text-strong);
  font-size: 16px;
}

.auth-feature-list p {
  margin: 10px 0 0;
  color: var(--text-sub);
  font-size: 13px;
  line-height: 1.8;
}

.auth-tabs {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(244, 247, 255, 0.96);
}

.auth-tabs button {
  min-width: 88px;
  min-height: 40px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--text-sub);
  font-weight: 700;
}

.auth-tabs button.is-active {
  color: var(--blue);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: var(--shadow-sm);
}

.auth-panel__head {
  margin-top: 24px;
}

.auth-form {
  display: grid;
  gap: 16px;
  margin-top: 24px;
}

.field-with-action {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.field-with-action__button {
  white-space: nowrap;
}

.auth-links {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.auth-links--single {
  justify-content: flex-start;
}

.auth-feedback {
  margin: 0;
  color: var(--rose);
  font-size: 13px;
  line-height: 1.7;
}

.auth-submit {
  width: 100%;
}

@media (max-width: 980px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }

  .auth-hero {
    min-height: auto;
    gap: 20px;
  }

  .auth-feature-list {
    grid-template-columns: 1fr;
  }

  .auth-hero h1 {
    font-size: 32px;
  }
}

@media (max-width: 640px) {
  .auth-hero,
  .auth-panel {
    padding: 20px;
  }

  .field-with-action {
    grid-template-columns: 1fr;
  }
}
</style>
