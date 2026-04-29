<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'
import { reactive, ref } from 'vue'

import { changePassword, logoutUser } from '../../services/auth'
import { updateHealthProfile, updateUserProfile, fetchUserProfileBundle } from '../../services/user'
import { getInitial, maskPhone, sanitizeVisibleText } from '../../utils/display'
import { ensureLogin, uploadImage } from '../../utils/api'

const loading = ref(false)
const bundle = ref<any>(null)
const avatarUrl = ref('')

const baseForm = reactive({
  realName: '',
  gender: '男',
  age: '',
  phone: '',
  skinType: '混合偏敏',
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

function toast(title: string) {
  uni.showToast({ title, icon: 'none' })
}

function fillForm(data: any) {
  bundle.value = data
  avatarUrl.value = data.profile?.avatar_url || data.account?.avatar_url || ''
  baseForm.realName = sanitizeVisibleText(data.profile?.real_name)
  baseForm.gender = sanitizeVisibleText(data.profile?.gender, '男')
  baseForm.age = data.profile?.age ? String(data.profile.age) : ''
  baseForm.phone = data.account?.phone || data.profile?.phone || ''
  baseForm.skinType = sanitizeVisibleText(data.health_profile?.skin_type, '混合偏敏')
}

async function loadData() {
  if (!ensureLogin()) return

  try {
    loading.value = true
    const data = await fetchUserProfileBundle()
    fillForm(data)
  } finally {
    loading.value = false
  }
}

async function chooseAvatar() {
  uni.chooseImage({
    count: 1,
    success: async (res) => {
      try {
        const uploaded = await uploadImage(res.tempFilePaths[0])
        avatarUrl.value = uploaded.file_url
      } catch (error: any) {
        toast(error.message || '头像上传失败，请稍后重试')
      }
    },
  })
}

async function saveProfile() {
  if (!baseForm.realName.trim()) {
    toast('请输入姓名')
    return
  }

  try {
    await Promise.all([
      updateUserProfile({
        avatar_url: avatarUrl.value || undefined,
        real_name: baseForm.realName.trim(),
        gender: baseForm.gender,
        age: baseForm.age ? Number(baseForm.age) : null,
      }),
      updateHealthProfile({
        skin_type: baseForm.skinType,
      }),
    ])
    uni.showToast({ title: '保存成功', icon: 'success' })
    await loadData()
  } catch (error: any) {
    toast(error.message || '保存失败，请稍后重试')
  }
}

async function submitPassword() {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    toast('请完整填写修改密码所需信息')
    return
  }
  if (passwordForm.newPassword.length < 6) {
    toast('新密码长度不少于 6 位')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    toast('两次输入的新密码不一致')
    return
  }

  try {
    await changePassword({
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword,
      confirmPassword: passwordForm.confirmPassword,
    })
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    uni.showToast({ title: '密码修改成功', icon: 'success' })
  } catch (error: any) {
    toast(error.message || '密码修改失败，请稍后重试')
  }
}

function modifyPhone() {
  toast('修改手机号功能正在完善中，请联系平台管理员协助处理')
}

function confirmLogout() {
  uni.showModal({
    title: '确认退出登录？',
    content: '退出后需要重新登录。',
    success: async (res) => {
      if (!res.confirm) return
      await logoutUser()
      uni.reLaunch({ url: '/pages/login/index' })
    },
  })
}

onShow(() => {
  void loadData()
})
</script>

<template>
  <view class="page-wrap safe-top profile-page">
    <view class="surface-card profile-card">
      <view class="section-title">个人资料</view>
      <view class="section-subtitle">管理您的个人信息与账户安全。</view>
    </view>

    <view v-if="loading" class="surface-card profile-card">
      <view class="section-subtitle" style="margin-top: 0;">正在加载个人资料...</view>
    </view>

    <template v-else>
      <view class="surface-card profile-card">
        <view class="label">基础资料</view>
        <view class="avatar-row">
          <view v-if="avatarUrl" class="avatar-row__image">
            <image :src="avatarUrl" mode="aspectFill" class="avatar-row__img" />
          </view>
          <view v-else class="avatar-row__placeholder">{{ getInitial(baseForm.realName || bundle?.account?.username) }}</view>
          <view class="secondary-btn avatar-row__button" @click="chooseAvatar">更换头像</view>
        </view>

        <view class="profile-form">
          <view>
            <view class="label">姓名</view>
            <input v-model="baseForm.realName" class="input-box" placeholder="请输入姓名" />
          </view>
          <view>
            <view class="label">性别</view>
            <view class="chip-row" style="margin-top: 12rpx;">
              <view class="chip" :class="{ active: baseForm.gender === '女' }" @click="baseForm.gender = '女'">女</view>
              <view class="chip" :class="{ active: baseForm.gender === '男' }" @click="baseForm.gender = '男'">男</view>
            </view>
          </view>
          <view>
            <view class="label">年龄</view>
            <input v-model="baseForm.age" class="input-box" maxlength="3" placeholder="请输入年龄" />
          </view>
          <view>
            <view class="label">手机号</view>
            <input :value="baseForm.phone" class="input-box" disabled />
          </view>
          <view>
            <view class="label">皮肤类型</view>
            <input v-model="baseForm.skinType" class="input-box" placeholder="请输入皮肤类型" />
          </view>
        </view>

        <view class="primary-btn" style="margin-top: 24rpx;" @click="saveProfile">保存修改</view>
      </view>

      <view class="surface-card profile-card">
        <view class="label">修改密码</view>
        <view class="profile-form">
          <view>
            <view class="label">当前密码</view>
            <input v-model="passwordForm.oldPassword" password class="input-box" placeholder="请输入当前密码" />
          </view>
          <view>
            <view class="label">新密码</view>
            <input v-model="passwordForm.newPassword" password class="input-box" placeholder="请输入新密码" />
          </view>
          <view>
            <view class="label">确认新密码</view>
            <input v-model="passwordForm.confirmPassword" password class="input-box" placeholder="请再次输入新密码" />
          </view>
        </view>

        <view class="primary-btn" style="margin-top: 24rpx;" @click="submitPassword">修改密码</view>
      </view>

      <view class="surface-card profile-card">
        <view class="label">手机号验证</view>
        <view class="section-subtitle">绑定手机号：{{ maskPhone(baseForm.phone) || '--' }}</view>
        <view class="status-chip mint" style="display: inline-flex; margin-top: 12rpx;">已验证</view>
        <view class="secondary-btn" style="margin-top: 20rpx;" @click="modifyPhone">修改手机号</view>
      </view>

      <view class="surface-card profile-card">
        <view class="label">退出登录</view>
        <view class="section-subtitle">退出后需要重新登录。</view>
        <view class="secondary-btn" style="margin-top: 20rpx;" @click="confirmLogout">退出登录</view>
      </view>
    </template>
  </view>
</template>

<style scoped lang="scss">
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.profile-card {
  padding: 28rpx;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 18rpx;
}

.avatar-row__image,
.avatar-row__placeholder {
  width: 120rpx;
  height: 120rpx;
  border-radius: 30rpx;
  overflow: hidden;
}

.avatar-row__img {
  width: 100%;
  height: 100%;
}

.avatar-row__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #2879ff, #5097ff 42%, #1cc9c2);
}

.avatar-row__button {
  flex: 1;
}

.profile-form {
  display: grid;
  gap: 18rpx;
  margin-top: 20rpx;
}

.chip.active {
  background: rgba(47, 125, 255, 0.16);
}
</style>
