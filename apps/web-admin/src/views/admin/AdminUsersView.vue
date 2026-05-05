<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  fetchAdminUserDetail,
  fetchAdminUsers,
  updateAdminUserStatus,
  type AdminUserDetail,
  type AdminUserListItem,
} from '@/api/workspace'
import { cleanVisibleText, formatDateTime, healthScoreTone, resolveAvatar, riskLabel, riskTone, splitVisibleText } from '@/utils/workspace'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detailLoading = ref(false)
const filters = reactive({
  keyword: '',
  status: null as number | null,
})

const users = ref<AdminUserListItem[]>([])
const detail = ref<AdminUserDetail | null>(null)

async function loadUsers() {
  try {
    loading.value = true
    const result = await fetchAdminUsers({
      page: 1,
      page_size: 30,
      keyword: filters.keyword || undefined,
      status: filters.status,
    })
    users.value = result.list
    const routeId = Number(route.params.userId)
    const matched = routeId ? result.list.find((item) => item.account.account_id === routeId) : null
    const targetId = matched?.account.account_id || result.list[0]?.account.account_id
    if (targetId && targetId !== routeId) {
      router.replace(`/admin/users/${targetId}`)
    } else if (!targetId) {
      detail.value = null
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadDetail(userId: number) {
  try {
    detailLoading.value = true
    detail.value = await fetchAdminUserDetail(userId)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    detailLoading.value = false
  }
}

async function toggleStatus(userId: number, status: number) {
  try {
    await updateAdminUserStatus(userId, status)
    ElMessage.success(status === 1 ? '用户已启用。' : '用户已停用。')
    await loadUsers()
    if (detail.value?.account.account_id === userId) {
      await loadDetail(userId)
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

function selectUser(userId: number) {
  router.replace(`/admin/users/${userId}`)
}

watch(
  () => route.params.userId,
  async (value) => {
    const userId = Number(value)
    if (userId) {
      await loadDetail(userId)
    }
  },
)

onMounted(loadUsers)
</script>

<template>
  <section class="two-panel-layout">
    <PanelCard title="用户管理" subtitle="支持账号筛选、状态管理，并可查看用户最近咨询记录。">
      <div class="filters-grid filters-grid--triple">
        <div class="form-field">
          <label>搜索用户</label>
          <input
            v-model="filters.keyword"
            class="ghost-input"
            placeholder="用户名、手机号、真实姓名"
            @keydown.enter.prevent="loadUsers"
          />
        </div>
        <div class="form-field">
          <label>状态</label>
          <el-select v-model="filters.status" clearable placeholder="全部状态">
            <el-option label="正常" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </div>
        <div class="action-row action-row--bottom">
          <button type="button" class="primary-button" @click="loadUsers">刷新列表</button>
        </div>
      </div>

      <div v-if="users.length" class="table-shell" style="margin-top: 18px;" v-loading="loading">
        <div class="table-head" style="--columns: 1.2fr 1fr 0.9fr 1.1fr 0.9fr 1fr;">
          <span>用户</span>
          <span>联系方式</span>
          <span>城市</span>
          <span>最近问诊</span>
          <span>状态</span>
          <span>操作</span>
        </div>

        <div
          v-for="item in users"
          :key="item.account.account_id"
          class="table-row table-row--clickable"
          style="--columns: 1.2fr 1fr 0.9fr 1.1fr 0.9fr 1fr;"
          @click="selectUser(item.account.account_id)"
        >
          <div>
            <strong>{{ item.profile.real_name || item.account.username }}</strong>
            <span class="table-cell__sub">UID {{ item.account.account_id }}</span>
          </div>
          <div>
            <div>{{ item.account.phone || '--' }}</div>
            <span class="table-cell__sub">{{ item.account.email || '--' }}</span>
          </div>
          <div>{{ item.profile.city || '--' }}</div>
          <div>
            <div>{{ cleanVisibleText(item.stats.latest_case_title, '暂无问诊') }}</div>
            <span class="table-cell__sub">{{ item.stats.latest_case_time || '--' }}</span>
          </div>
          <div>
            <StatusBadge :label="item.account.status === 1 ? '正常' : '停用'" :tone="item.account.status === 1 ? 'mint' : 'rose'" />
          </div>
          <div class="action-row">
            <button
              type="button"
              class="soft-button"
              @click.stop="toggleStatus(item.account.account_id, item.account.status === 1 ? 0 : 1)"
            >
              {{ item.account.status === 1 ? '停用' : '启用' }}
            </button>
          </div>
        </div>
      </div>
      <EmptyState v-else title="当前没有匹配用户" copy="可以调整筛选条件，或等待新的用户数据接入。" />
    </PanelCard>

    <PanelCard v-if="detail" title="用户详情" subtitle="展示基础信息、健康档案与最近咨询，方便管理核查。">
      <div v-loading="detailLoading">
        <div class="detail-card">
          <div class="avatar-row">
            <img :src="resolveAvatar(detail.account.avatar_url, detail.profile.real_name || detail.account.username)" :alt="detail.profile.real_name || detail.account.username" />
            <div>
              <strong>{{ detail.profile.real_name || detail.account.username }}</strong>
              <span>{{ detail.profile.gender || '未设置' }} · {{ detail.profile.age || '--' }} 岁 · {{ detail.profile.city || '未设置城市' }}</span>
            </div>
          </div>
          <div class="action-row" style="margin-top: 14px;">
            <StatusBadge :label="detail.account.status === 1 ? '账号正常' : '账号停用'" :tone="detail.account.status === 1 ? 'mint' : 'rose'" />
            <StatusBadge :label="`健康评分 ${detail.health_score}`" :tone="healthScoreTone(detail.health_score)" />
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">基础信息</div>
          <div class="key-value" style="margin-top: 10px;">
            <div class="key-value__row">
              <span>手机号</span>
              <strong>{{ detail.account.phone || '--' }}</strong>
            </div>
            <div class="key-value__row">
              <span>邮箱</span>
              <strong>{{ detail.account.email || '--' }}</strong>
            </div>
            <div class="key-value__row">
              <span>肤质</span>
              <strong>{{ detail.health_profile.skin_type || '未完善' }}</strong>
            </div>
            <div class="key-value__row">
              <span>过敏史</span>
              <strong>{{ splitVisibleText(detail.health_profile.allergy_history).join('、') || '无' }}</strong>
            </div>
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">最近咨询记录</div>
          <div v-if="detail.recent_consultations.length" class="list-panel" style="margin-top: 14px;">
            <article v-for="item in detail.recent_consultations.slice(0, 5)" :key="item.case_id" class="list-row">
              <div class="list-row__head">
                <div>
                  <strong>{{ cleanVisibleText(item.summary_title, '皮肤健康咨询') }}</strong>
                  <span>{{ formatDateTime(item.submitted_at) }}</span>
                </div>
                <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
              </div>
              <p class="list-row__summary">{{ cleanVisibleText(item.chief_complaint, '患者未补充更多主诉。') }}</p>
            </article>
          </div>
          <EmptyState v-else title="暂无咨询记录" copy="当前用户还没有形成可展示的问诊记录。" />
        </div>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无用户详情" subtitle="从左侧列表选择用户后，可查看完整档案。">
      <EmptyState title="请选择用户" copy="点击左侧某位用户，即可查看其基础信息与最近咨询记录。" />
    </PanelCard>
  </section>
</template>
