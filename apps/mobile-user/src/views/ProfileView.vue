<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import PageState from '../components/PageState.vue'
import { changePassword, logoutUser } from '../services/auth'
import { uploadImage } from '../services/api'
import { fetchUserProfileBundle, updateHealthProfile, updateUserProfile, type UserProfileBundle } from '../services/user'
import { getInitial, maskPhone, sanitizeVisibleText } from '../utils/display'

const router = useRouter()

const fileInputRef = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const saveLoading = ref(false)
const avatarUploading = ref(false)
const passwordLoading = ref(false)
const logoutLoading = ref(false)
const logoutDialogOpen = ref(false)
const profileBundle = ref<UserProfileBundle | null>(null)

const baseForm = reactive({
  avatarUrl: '',
  realName: '',
  gender: '男',
  age: '',
  phone: '',
  skinType: '',
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const skinTypeOptions = ['混合偏敏', '油性肌肤', '干性肌肤', '中性肌肤', '敏感肌']

const avatarDisplay = computed(() => {
  const name = sanitizeVisibleText(baseForm.realName || profileBundle.value?.account.username, '用户')
  return {
    url: baseForm.avatarUrl,
    text: getInitial(name),
  }
})

function fillForm(bundle: UserProfileBundle) {
  baseForm.avatarUrl = bundle.profile.avatar_url || bundle.account.avatar_url || ''
  baseForm.realName = sanitizeVisibleText(bundle.profile.real_name)
  baseForm.gender = sanitizeVisibleText(bundle.profile.gender, '男')
  baseForm.age = bundle.profile.age ? String(bundle.profile.age) : ''
  baseForm.phone = bundle.account.phone || bundle.profile.phone || ''
  baseForm.skinType = sanitizeVisibleText(bundle.health_profile.skin_type, '混合偏敏')
}

async function loadProfile() {
  try {
    loading.value = true
    errorMessage.value = ''
    const response = await fetchUserProfileBundle()
    profileBundle.value = response
    fillForm(response)
  } catch (error) {
    errorMessage.value = (error as Error).message || '个人资料加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function openAvatarPicker() {
  fileInputRef.value?.click()
}

async function handleAvatarChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''

  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    window.alert('仅支持 JPG、PNG、WebP 格式的头像图片。')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    window.alert('头像图片不能超过 10MB。')
    return
  }

  try {
    avatarUploading.value = true
    const uploaded = await uploadImage(file)
    baseForm.avatarUrl = uploaded.file_url
  } catch (error) {
    window.alert((error as Error).message || '头像上传失败，请稍后重试。')
  } finally {
    avatarUploading.value = false
  }
}

async function saveProfile() {
  if (!baseForm.realName.trim()) {
    window.alert('请输入姓名。')
    return
  }

  try {
    saveLoading.value = true
    await Promise.all([
      updateUserProfile({
        avatar_url: baseForm.avatarUrl || undefined,
        real_name: baseForm.realName.trim(),
        gender: baseForm.gender,
        age: baseForm.age ? Number(baseForm.age) : null,
      }),
      updateHealthProfile({
        skin_type: baseForm.skinType,
      }),
    ])
    window.alert('保存成功')
    await loadProfile()
  } catch (error) {
    window.alert((error as Error).message || '保存失败，请稍后重试。')
  } finally {
    saveLoading.value = false
  }
}

async function submitPassword() {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    window.alert('请完整填写修改密码所需信息。')
    return
  }
  if (passwordForm.newPassword.length < 6) {
    window.alert('新密码长度不少于 6 位。')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    window.alert('两次输入的新密码不一致。')
    return
  }

  try {
    passwordLoading.value = true
    await changePassword({
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword,
      confirmPassword: passwordForm.confirmPassword,
    })
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    window.alert('密码修改成功')
  } catch (error) {
    window.alert((error as Error).message || '密码修改失败，请稍后重试。')
  } finally {
    passwordLoading.value = false
  }
}

function handleChangePhone() {
  window.alert('修改手机号功能正在完善中，当前请联系平台管理员协助处理。')
}

async function handleLogout() {
  try {
    logoutLoading.value = true
    await logoutUser()
    logoutDialogOpen.value = false
    router.replace('/login')
  } finally {
    logoutLoading.value = false
  }
}

onMounted(() => {
  void loadProfile()
})
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <p class="section-eyebrow">个人资料</p>
      <h1 class="section-title">管理您的个人信息与账户安全。</h1>
    </article>

    <PageState
      v-if="loading"
      title="正在加载个人资料"
      description="请稍候，我们正在同步您的账户信息。"
    />

    <PageState
      v-else-if="errorMessage"
      tone="error"
      title="个人资料加载失败"
      :description="errorMessage"
      action-text="重新加载"
      @action="loadProfile"
    />

    <template v-else>
      <div class="grid-2 profile-grid">
        <article class="surface-card">
          <div class="section-head">
            <div>
              <p class="section-eyebrow">基础资料</p>
              <h2 class="card-title">完善个人信息，便于获得更准确的服务。</h2>
            </div>
          </div>

          <div class="profile-avatar">
            <input ref="fileInputRef" type="file" accept="image/jpeg,image/png,image/webp" class="profile-avatar__input" @change="handleAvatarChange" />
            <div v-if="avatarDisplay.url" class="profile-avatar__image">
              <img :src="avatarDisplay.url" alt="头像" />
            </div>
            <div v-else class="profile-avatar__placeholder">{{ avatarDisplay.text }}</div>
            <button type="button" class="secondary-button" :disabled="avatarUploading" @click="openAvatarPicker">
              {{ avatarUploading ? '上传中...' : '更换头像' }}
            </button>
          </div>

          <div class="profile-form">
            <div class="field">
              <label>姓名</label>
              <input v-model="baseForm.realName" class="ghost-input" placeholder="请输入姓名" />
            </div>

            <div class="field">
              <label>性别</label>
              <div class="profile-choice-group">
                <button type="button" :class="{ 'is-active': baseForm.gender === '女' }" @click="baseForm.gender = '女'">女</button>
                <button type="button" :class="{ 'is-active': baseForm.gender === '男' }" @click="baseForm.gender = '男'">男</button>
              </div>
            </div>

            <div class="field">
              <label>年龄</label>
              <input v-model="baseForm.age" class="ghost-input" inputmode="numeric" placeholder="请输入年龄" />
            </div>

            <div class="field">
              <label>手机号</label>
              <input :value="baseForm.phone" class="ghost-input" disabled />
            </div>

            <div class="field">
              <label>皮肤类型</label>
              <select v-model="baseForm.skinType" class="ghost-select">
                <option v-for="item in skinTypeOptions" :key="item" :value="item">{{ item }}</option>
              </select>
            </div>
          </div>

          <button type="button" class="primary-button profile-submit" :disabled="saveLoading" @click="saveProfile">
            {{ saveLoading ? '保存中...' : '保存修改' }}
          </button>
        </article>

        <div class="profile-side">
          <article class="surface-card">
            <div class="section-head">
              <div>
                <p class="section-eyebrow">账户安全</p>
                <h2 class="card-title">建议定期修改密码，保护账户安全。</h2>
              </div>
            </div>

            <div class="page-stack">
              <div class="field">
                <label>当前密码</label>
                <input v-model="passwordForm.oldPassword" class="ghost-input" type="password" placeholder="请输入当前密码" />
              </div>

              <div class="field">
                <label>新密码</label>
                <input v-model="passwordForm.newPassword" class="ghost-input" type="password" placeholder="请输入新密码" />
              </div>

              <div class="field">
                <label>确认新密码</label>
                <input v-model="passwordForm.confirmPassword" class="ghost-input" type="password" placeholder="请再次输入新密码" />
              </div>
            </div>

            <button type="button" class="primary-button profile-submit" :disabled="passwordLoading" @click="submitPassword">
              {{ passwordLoading ? '提交中...' : '修改密码' }}
            </button>
          </article>

          <article class="surface-card">
            <div class="section-head">
              <div>
                <p class="section-eyebrow">手机号验证</p>
                <h2 class="card-title">绑定手机号：{{ maskPhone(baseForm.phone) || '--' }}</h2>
              </div>
              <span class="risk-badge" data-tone="mint">已验证</span>
            </div>
            <button type="button" class="secondary-button" @click="handleChangePhone">修改手机号</button>
          </article>

          <article class="surface-card">
            <div class="section-head">
              <div>
                <p class="section-eyebrow">退出登录</p>
                <h2 class="card-title">退出后需要重新登录</h2>
              </div>
            </div>
            <button type="button" class="secondary-button" @click="logoutDialogOpen = true">退出登录</button>
          </article>
        </div>
      </div>
    </template>

    <ConfirmDialog
      :visible="logoutDialogOpen"
      title="确认退出登录？"
      description="退出后需要重新登录。"
      confirm-text="确认退出"
      cancel-text="取消"
      :loading="logoutLoading"
      @cancel="logoutDialogOpen = false"
      @confirm="handleLogout"
    />
  </section>
</template>

<style scoped>
.profile-grid {
  align-items: start;
}

.profile-avatar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.profile-avatar__input {
  display: none;
}

.profile-avatar__image,
.profile-avatar__placeholder {
  width: 84px;
  height: 84px;
  border-radius: 22px;
  overflow: hidden;
}

.profile-avatar__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-avatar__placeholder {
  display: inline-grid;
  place-items: center;
  color: #ffffff;
  font-size: 24px;
  font-weight: 700;
  background: var(--gradient-main);
}

.profile-form,
.profile-side {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.profile-choice-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.profile-choice-group button {
  min-height: 44px;
  padding: 0 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--text-sub);
  font-weight: 700;
}

.profile-choice-group button.is-active {
  border-color: rgba(47, 125, 255, 0.48);
  background: rgba(47, 125, 255, 0.1);
  color: var(--blue);
}

.profile-submit {
  width: 100%;
  margin-top: 18px;
}
</style>
