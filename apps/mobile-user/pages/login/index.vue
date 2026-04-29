<script setup lang="ts">
import { onUnload } from '@dcloudio/uni-app'
import { computed, reactive, ref } from 'vue'

import { loginUser, registerUser, resetPassword, sendVerificationCode } from '../../services/auth'

type AuthMode = 'login' | 'register' | 'reset'

const activeMode = ref<AuthMode>('login')
const loading = ref(false)
const codeSending = ref(false)
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

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

const subtitle = computed(() => {
  if (activeMode.value === 'register') return '填写手机号、验证码和密码，完成账户注册。'
  if (activeMode.value === 'reset') return '通过验证码重置密码，重新登录您的账户。'
  return '请输入手机号和密码，继续使用肤联智诊。'
})

function setMode(mode: AuthMode) {
  activeMode.value = mode
}

function isValidPhone(phone: string) {
  return /^1\d{10}$/.test(phone.trim())
}

function toast(title: string) {
  uni.showToast({ title, icon: 'none' })
}

function startCooldown(seconds = 60) {
  cooldown.value = seconds
  if (timer) clearInterval(timer)
  timer = setInterval(() => {
    cooldown.value = Math.max(0, cooldown.value - 1)
    if (cooldown.value === 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

async function requestCode(scene: 'REGISTER' | 'RESET_PASSWORD') {
  const phone = scene === 'REGISTER' ? registerForm.phone : resetForm.phone
  if (!isValidPhone(phone)) {
    toast('请输入正确的手机号')
    return
  }

  try {
    codeSending.value = true
    const response = await sendVerificationCode(phone.trim(), scene)
    startCooldown(Math.min(response.expires_in || 60, 60))
    uni.showToast({ title: '验证码请求已提交', icon: 'success' })
  } catch (error: any) {
    toast(error.message || '验证码发送失败')
  } finally {
    codeSending.value = false
  }
}

async function submitLogin() {
  if (!isValidPhone(loginForm.phone)) {
    toast('请输入正确的手机号')
    return
  }
  if (!loginForm.password) {
    toast('请输入密码')
    return
  }

  try {
    loading.value = true
    await loginUser(loginForm.phone.trim(), loginForm.password)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/consultation/index' })
    }, 250)
  } catch (error: any) {
    toast(error.message || '登录失败，请检查手机号和密码')
  } finally {
    loading.value = false
  }
}

async function submitRegister() {
  if (!isValidPhone(registerForm.phone)) {
    toast('请输入正确的手机号')
    return
  }
  if (!registerForm.code) {
    toast('请输入验证码')
    return
  }
  if (registerForm.password.length < 6) {
    toast('密码长度不少于 6 位')
    return
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    toast('两次输入的密码不一致')
    return
  }

  try {
    loading.value = true
    await registerUser({
      phone: registerForm.phone.trim(),
      code: registerForm.code.trim(),
      password: registerForm.password,
    })
    await loginUser(registerForm.phone.trim(), registerForm.password)
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/consultation/index' })
    }, 250)
  } catch (error: any) {
    toast(error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function submitReset() {
  if (!isValidPhone(resetForm.phone)) {
    toast('请输入正确的手机号')
    return
  }
  if (!resetForm.code) {
    toast('请输入验证码')
    return
  }
  if (resetForm.password.length < 6) {
    toast('新密码长度不少于 6 位')
    return
  }
  if (resetForm.password !== resetForm.confirmPassword) {
    toast('两次输入的新密码不一致')
    return
  }

  try {
    loading.value = true
    await resetPassword({
      phone: resetForm.phone.trim(),
      code: resetForm.code.trim(),
      password: resetForm.password,
    })
    loginForm.phone = resetForm.phone.trim()
    loginForm.password = ''
    setMode('login')
    uni.showToast({ title: '密码修改成功', icon: 'success' })
  } catch (error: any) {
    toast(error.message || '密码重置失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function handleSubmit() {
  if (activeMode.value === 'register') {
    return submitRegister()
  }
  if (activeMode.value === 'reset') {
    return submitReset()
  }
  return submitLogin()
}

onUnload(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <view class="page-wrap safe-top login-page">
    <view class="surface-card login-card">
      <view class="login-brand">肤联智诊</view>
      <view class="section-title">智能问诊 · 皮肤健康管理</view>
      <view class="section-subtitle">上传皮肤图片，补充症状信息，查看智能分析结果，并持续接收医生回复和护理建议。</view>

      <view class="chip-row login-tags">
        <view class="chip">安全问诊</view>
        <view class="chip">专业建议</view>
        <view class="chip">隐私保护</view>
      </view>

      <view class="login-tabs">
        <view :class="{ active: activeMode === 'login' }" @click="setMode('login')">登录</view>
        <view :class="{ active: activeMode === 'register' }" @click="setMode('register')">注册</view>
      </view>

      <view class="section-subtitle">{{ subtitle }}</view>

      <view class="login-form">
        <template v-if="activeMode === 'login'">
          <view>
            <view class="label">手机号</view>
            <input v-model="loginForm.phone" class="input-box" maxlength="11" placeholder="请输入手机号" />
          </view>
          <view>
            <view class="label">密码</view>
            <input v-model="loginForm.password" password class="input-box" placeholder="请输入密码" />
          </view>
          <view class="login-links">
            <view class="text-btn" @click="setMode('reset')">忘记密码</view>
            <view class="text-btn" @click="setMode('register')">立即注册</view>
          </view>
        </template>

        <template v-else-if="activeMode === 'register'">
          <view>
            <view class="label">手机号</view>
            <input v-model="registerForm.phone" class="input-box" maxlength="11" placeholder="请输入手机号" />
          </view>
          <view>
            <view class="label">验证码</view>
            <view class="inline-row">
              <input v-model="registerForm.code" class="input-box inline-row__input" maxlength="6" placeholder="请输入验证码" />
              <view class="secondary-btn inline-row__button" @click="cooldown === 0 && !codeSending && requestCode('REGISTER')">
                {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
              </view>
            </view>
          </view>
          <view>
            <view class="label">密码</view>
            <input v-model="registerForm.password" password class="input-box" placeholder="请输入密码" />
          </view>
          <view>
            <view class="label">确认密码</view>
            <input v-model="registerForm.confirmPassword" password class="input-box" placeholder="请再次输入密码" />
          </view>
          <view class="text-btn" @click="setMode('login')">已有账号？去登录</view>
        </template>

        <template v-else>
          <view>
            <view class="label">手机号</view>
            <input v-model="resetForm.phone" class="input-box" maxlength="11" placeholder="请输入手机号" />
          </view>
          <view>
            <view class="label">验证码</view>
            <view class="inline-row">
              <input v-model="resetForm.code" class="input-box inline-row__input" maxlength="6" placeholder="请输入验证码" />
              <view class="secondary-btn inline-row__button" @click="cooldown === 0 && !codeSending && requestCode('RESET_PASSWORD')">
                {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
              </view>
            </view>
          </view>
          <view>
            <view class="label">新密码</view>
            <input v-model="resetForm.password" password class="input-box" placeholder="请输入新密码" />
          </view>
          <view>
            <view class="label">确认新密码</view>
            <input v-model="resetForm.confirmPassword" password class="input-box" placeholder="请再次输入新密码" />
          </view>
          <view class="text-btn" @click="setMode('login')">返回登录</view>
        </template>

        <view class="primary-btn login-submit" @click="handleSubmit">
          {{ loading ? '提交中...' : activeMode === 'register' ? '创建账号' : activeMode === 'reset' ? '确认修改' : '登录' }}
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.login-page {
  display: flex;
  align-items: center;
}

.login-card {
  width: 100%;
  padding: 34rpx;
}

.login-brand {
  color: #15326a;
  font-size: 52rpx;
  font-weight: 700;
}

.login-tags {
  margin-top: 24rpx;
}

.login-tabs {
  display: flex;
  gap: 12rpx;
  margin-top: 30rpx;
  padding: 8rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 999rpx;
  background: rgba(244, 247, 255, 0.96);
}

.login-tabs view {
  flex: 1;
  min-height: 74rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999rpx;
  color: #5a7298;
  font-size: 28rpx;
  font-weight: 700;
}

.login-tabs .active {
  color: #2f7dff;
  background: rgba(255, 255, 255, 0.98);
}

.login-form {
  display: grid;
  gap: 20rpx;
  margin-top: 24rpx;
}

.inline-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220rpx;
  gap: 14rpx;
}

.inline-row__input {
  min-width: 0;
}

.inline-row__button {
  min-height: 88rpx;
}

.login-links {
  display: flex;
  justify-content: space-between;
}

.login-submit {
  margin-top: 8rpx;
}
</style>
