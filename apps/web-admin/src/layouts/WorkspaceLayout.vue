<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import BrandMark from '@/components/BrandMark.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { updateWorkspaceProfile } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

type NavItem = {
  label: string
  path: string
  keywords: string[]
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const profileDialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const savingProfile = ref(false)
const savingPassword = ref(false)

const profileForm = reactive({
  real_name: '',
  gender: '',
  age: undefined as number | undefined,
  birthday: '',
  city: '',
  occupation: '',
  emergency_contact: '',
  emergency_phone: '',
  remark: '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const doctorNav: NavItem[] = [
  { label: '工作台', path: '/doctor/workbench', keywords: ['工作台', '队列', '风险', '效率'] },
  { label: '问诊管理', path: '/doctor/consultations', keywords: ['问诊', '病例', 'AI', '回复'] },
  { label: '患者档案', path: '/doctor/patients', keywords: ['患者', '档案', '历史病例', '护理'] },
]

const adminNav: NavItem[] = [
  { label: '控制台', path: '/admin/dashboard', keywords: ['控制台', '运营', '趋势', '告警'] },
  { label: '用户管理', path: '/admin/users', keywords: ['用户', '账号', '停用', '详情'] },
  { label: '医生管理', path: '/admin/doctors', keywords: ['医生', '审核', '资质', '服务'] },
  { label: '咨询记录', path: '/admin/consultations', keywords: ['咨询', '问诊', '归档', '异常'] },
  { label: '系统配置', path: '/admin/settings', keywords: ['配置', '模型', '提示词', '权限'] },
  { label: '日志监控', path: '/admin/logs', keywords: ['日志', '监控', '告警', '异常'] },
]

const navItems = computed(() => (auth.role === 'ADMIN' ? adminNav : doctorNav))
const currentTitle = computed(() => String(route.meta.title || '工作空间'))
const currentSubtitle = computed(() => String(route.meta.subtitle || '查看当前角色下的核心业务模块。'))
const roleHomePath = computed(() => (auth.role === 'ADMIN' ? '/admin/dashboard' : '/doctor/workbench'))
const searchPlaceholder = computed(() => (
  auth.role === 'ADMIN'
    ? '搜索模块，如用户、医生、咨询记录、系统配置'
    : '搜索模块，如工作台、问诊管理、患者档案'
))
const roleSummary = computed(() => (
  auth.role === 'ADMIN'
    ? '负责平台账号治理、咨询监管、参数配置与日志监控。'
    : '负责图文问诊处理、患者长期档案和 AI 结果复核。'
))

const currentNav = computed(() => (
  navItems.value.find((item) => route.path.startsWith(item.path)) || navItems.value[0]
))

function syncProfileForm() {
  profileForm.real_name = auth.profile?.real_name || ''
  profileForm.gender = auth.profile?.gender || ''
  profileForm.age = auth.profile?.age || undefined
  profileForm.birthday = auth.profile?.birthday || ''
  profileForm.city = auth.profile?.city || ''
  profileForm.occupation = auth.profile?.occupation || ''
  profileForm.emergency_contact = auth.profile?.emergency_contact || ''
  profileForm.emergency_phone = auth.profile?.emergency_phone || ''
  profileForm.remark = auth.profile?.remark || ''
}

watch(profileDialogVisible, (visible) => {
  if (visible) {
    syncProfileForm()
  }
})

async function handleSearch() {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) {
    router.push(roleHomePath.value)
    return
  }

  const matched = navItems.value.find((item) => {
    return item.label.toLowerCase().includes(keyword)
      || item.keywords.some((entry) => entry.toLowerCase().includes(keyword))
  })

  if (matched) {
    router.push(matched.path)
    return
  }

  ElMessage.info('没有找到匹配模块，已返回当前角色首页。')
  router.push(roleHomePath.value)
}

async function saveProfile() {
  try {
    savingProfile.value = true
    await updateWorkspaceProfile({
      real_name: profileForm.real_name || undefined,
      gender: profileForm.gender || undefined,
      age: profileForm.age || null,
      birthday: profileForm.birthday || undefined,
      city: profileForm.city || undefined,
      occupation: profileForm.occupation || undefined,
      emergency_contact: profileForm.emergency_contact || undefined,
      emergency_phone: profileForm.emergency_phone || undefined,
      remark: profileForm.remark || undefined,
    })
    await auth.loadProfile()
    profileDialogVisible.value = false
    ElMessage.success('个人资料已更新。')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  try {
    savingPassword.value = true
    await auth.updatePassword(
      passwordForm.old_password,
      passwordForm.new_password,
      passwordForm.confirm_password,
    )
    passwordDialogVisible.value = false
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    ElMessage.success('密码修改成功。')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    savingPassword.value = false
  }
}

async function logout() {
  await auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="workspace-shell">
    <aside class="workspace-sidebar">
      <button type="button" class="brand-button" @click="router.push(roleHomePath)">
        <BrandMark />
      </button>

      <nav class="workspace-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="workspace-nav__item"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <section class="workspace-sidebar__assistant">
        <div class="workspace-sidebar__assistant-badge">{{ auth.roleLabel }}</div>
        <strong>{{ currentNav?.label }}</strong>
        <p>{{ roleSummary }}</p>
      </section>
    </aside>

    <main class="workspace-main">
      <header class="workspace-topbar">
        <div>
          <div class="workspace-topbar__eyebrow">
            {{ auth.role === 'ADMIN' ? '管理运营中台' : '医生工作空间' }}
          </div>
          <h1>{{ currentTitle }}</h1>
          <p>{{ currentSubtitle }}</p>
        </div>

        <div class="workspace-topbar__actions">
          <div class="workspace-topbar__search">
            <input
              v-model="searchQuery"
              :placeholder="searchPlaceholder"
              @keydown.enter.prevent="handleSearch"
            />
          </div>

          <StatusBadge :label="auth.roleLabel" :tone="auth.role === 'ADMIN' ? 'violet' : 'blue'" />

          <div class="workspace-topbar__profile">
            <img :src="auth.avatar" :alt="auth.displayName" />
            <div>
              <strong>{{ auth.displayName }}</strong>
              <span>{{ auth.title }}</span>
            </div>
          </div>

          <div class="action-row">
            <button type="button" class="ghost-button" @click="profileDialogVisible = true">个人资料</button>
            <button type="button" class="ghost-button" @click="passwordDialogVisible = true">修改密码</button>
            <button type="button" class="primary-button" @click="logout">退出登录</button>
          </div>
        </div>
      </header>

      <section class="workspace-content">
        <RouterView />
      </section>
    </main>
  </div>

  <el-dialog
    v-model="profileDialogVisible"
    title="个人资料"
    width="720px"
    destroy-on-close
  >
    <div class="dialog-grid">
      <div class="form-field">
        <label>姓名</label>
        <input v-model="profileForm.real_name" class="ghost-input" placeholder="请输入姓名" />
      </div>
      <div class="form-field">
        <label>性别</label>
        <el-select v-model="profileForm.gender" placeholder="请选择性别" clearable>
          <el-option label="女" value="女" />
          <el-option label="男" value="男" />
          <el-option label="未设置" value="" />
        </el-select>
      </div>
      <div class="form-field">
        <label>年龄</label>
        <el-input-number v-model="profileForm.age" :min="0" :max="120" :controls="false" style="width: 100%;" />
      </div>
      <div class="form-field">
        <label>生日</label>
        <input v-model="profileForm.birthday" class="ghost-input" placeholder="YYYY-MM-DD" />
      </div>
      <div class="form-field">
        <label>所在城市</label>
        <input v-model="profileForm.city" class="ghost-input" placeholder="请输入城市" />
      </div>
      <div class="form-field">
        <label>职业</label>
        <input v-model="profileForm.occupation" class="ghost-input" placeholder="请输入职业" />
      </div>
      <div class="form-field">
        <label>紧急联系人</label>
        <input v-model="profileForm.emergency_contact" class="ghost-input" placeholder="请输入联系人姓名" />
      </div>
      <div class="form-field">
        <label>紧急联系电话</label>
        <input v-model="profileForm.emergency_phone" class="ghost-input" placeholder="请输入联系电话" />
      </div>
      <div class="form-field dialog-grid__full">
        <label>备注</label>
        <textarea v-model="profileForm.remark" class="ghost-textarea" placeholder="补充说明当前角色的资料信息" />
      </div>
    </div>

    <template #footer>
      <div class="action-row" style="justify-content: flex-end;">
        <button type="button" class="ghost-button" @click="profileDialogVisible = false">取消</button>
        <button type="button" class="primary-button" :disabled="savingProfile" @click="saveProfile">
          {{ savingProfile ? '保存中…' : '保存资料' }}
        </button>
      </div>
    </template>
  </el-dialog>

  <el-dialog
    v-model="passwordDialogVisible"
    title="修改密码"
    width="520px"
    destroy-on-close
  >
    <div class="dialog-grid dialog-grid--single">
      <div class="form-field">
        <label>原密码</label>
        <input v-model="passwordForm.old_password" class="ghost-input" type="password" placeholder="请输入原密码" />
      </div>
      <div class="form-field">
        <label>新密码</label>
        <input v-model="passwordForm.new_password" class="ghost-input" type="password" placeholder="至少 8 位" />
      </div>
      <div class="form-field">
        <label>确认新密码</label>
        <input v-model="passwordForm.confirm_password" class="ghost-input" type="password" placeholder="再次输入新密码" />
      </div>
    </div>

    <template #footer>
      <div class="action-row" style="justify-content: flex-end;">
        <button type="button" class="ghost-button" @click="passwordDialogVisible = false">取消</button>
        <button type="button" class="primary-button" :disabled="savingPassword" @click="savePassword">
          {{ savingPassword ? '提交中…' : '确认修改' }}
        </button>
      </div>
    </template>
  </el-dialog>
</template>
