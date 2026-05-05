<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import EmptyState from '@/components/EmptyState.vue'
import PanelCard from '@/components/PanelCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import {
  auditAdminDoctor,
  fetchAdminDoctorDetail,
  fetchAdminDoctors,
  updateAdminDoctorStatus,
  type AdminDoctorDetail,
  type AdminDoctorListItem,
} from '@/api/workspace'
import {
  auditStatusLabel,
  auditStatusTone,
  cleanVisibleText,
  formatDateTime,
  riskLabel,
  riskTone,
  resolveAvatar,
  serviceStatusLabel,
  serviceStatusTone,
  splitVisibleText,
  statusLabel,
  statusTone,
} from '@/utils/workspace'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detailLoading = ref(false)
const filters = reactive({
  keyword: '',
  audit_status: '',
  service_status: null as number | null,
})

const doctors = ref<AdminDoctorListItem[]>([])
const detail = ref<AdminDoctorDetail | null>(null)

async function loadDoctors() {
  try {
    loading.value = true
    const result = await fetchAdminDoctors({
      page: 1,
      page_size: 40,
      keyword: filters.keyword || undefined,
      audit_status: filters.audit_status || undefined,
      service_status: filters.service_status,
    })
    doctors.value = result.list
    const routeId = Number(route.params.doctorId)
    const matched = routeId ? result.list.find((item) => item.doctor_id === routeId) : null
    const targetId = matched?.doctor_id || result.list[0]?.doctor_id
    if (targetId && routeId !== targetId) {
      router.replace(`/admin/doctors/${targetId}`)
    } else if (!targetId) {
      detail.value = null
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadDetail(doctorId: number) {
  try {
    detailLoading.value = true
    detail.value = await fetchAdminDoctorDetail(doctorId)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    detailLoading.value = false
  }
}

async function handleAudit(doctorId: number, auditStatus: string) {
  try {
    await auditAdminDoctor(doctorId, { audit_status: auditStatus })
    ElMessage.success('审核状态已更新。')
    await loadDoctors()
    await loadDetail(doctorId)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function handleService(doctorId: number, status: number) {
  try {
    await updateAdminDoctorStatus(doctorId, status)
    ElMessage.success(status === 1 ? '已恢复服务。' : '已暂停服务。')
    await loadDoctors()
    await loadDetail(doctorId)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

function selectDoctor(doctorId: number) {
  router.replace(`/admin/doctors/${doctorId}`)
}

watch(
  () => route.params.doctorId,
  async (value) => {
    const doctorId = Number(value)
    if (doctorId) {
      await loadDetail(doctorId)
    }
  },
)

onMounted(loadDoctors)
</script>

<template>
  <section class="two-panel-layout">
    <PanelCard title="医生管理" subtitle="支持资质审核、服务状态管理，并可查看医生处理能力与最近咨询。">
      <div class="filters-grid filters-grid--triple">
        <div class="form-field">
          <label>搜索医生</label>
          <input
            v-model="filters.keyword"
            class="ghost-input"
            placeholder="姓名、医院、科室、手机号"
            @keydown.enter.prevent="loadDoctors"
          />
        </div>
        <div class="form-field">
          <label>审核状态</label>
          <el-select v-model="filters.audit_status" clearable placeholder="全部状态">
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已驳回" value="REJECTED" />
          </el-select>
        </div>
        <div class="form-field">
          <label>服务状态</label>
          <el-select v-model="filters.service_status" clearable placeholder="全部状态">
            <el-option label="服务中" :value="1" />
            <el-option label="已暂停" :value="0" />
          </el-select>
        </div>
      </div>

      <div class="action-row" style="margin-top: 14px;">
        <button type="button" class="primary-button" @click="loadDoctors">刷新列表</button>
      </div>

      <div v-if="doctors.length" class="list-panel" style="margin-top: 18px;" v-loading="loading">
        <article
          v-for="item in doctors"
          :key="item.doctor_id"
          class="list-row"
          :class="{ 'is-active': detail?.doctor.doctor_id === item.doctor_id }"
          @click="selectDoctor(item.doctor_id)"
        >
          <div class="list-row__head">
            <div class="avatar-row">
              <img :src="resolveAvatar(item.account.avatar_url, item.doctor_name)" :alt="item.doctor_name" />
              <div>
                <strong>{{ item.doctor_name }}</strong>
                <span>{{ item.hospital_name || '未完善执业机构' }} · {{ item.department || '未设置科室' }}</span>
              </div>
            </div>
            <div class="action-row">
              <StatusBadge :label="auditStatusLabel(item.audit_status)" :tone="auditStatusTone(item.audit_status)" />
              <StatusBadge :label="serviceStatusLabel(item.service_status)" :tone="serviceStatusTone(item.service_status)" />
            </div>
          </div>

          <p class="list-row__summary">{{ cleanVisibleText(item.specialty, '待补充擅长方向') }}</p>
          <div class="summary-grid">
            <div><span>回复率</span><strong>{{ item.stats.response_rate }}%</strong></div>
            <div><span>处理问诊</span><strong>{{ item.stats.consultation_total }}</strong></div>
          </div>
        </article>
      </div>
      <EmptyState v-else title="当前没有匹配医生" copy="可以调整筛选条件，或等待新的医生资料接入。" />
    </PanelCard>

    <PanelCard v-if="detail" title="医生详情" subtitle="查看医生基础信息、审核备注、服务状态与最近处理记录。">
      <div v-loading="detailLoading">
        <div class="detail-card">
          <div class="avatar-row">
            <img :src="resolveAvatar(detail.account.avatar_url, detail.doctor.doctor_name)" :alt="detail.doctor.doctor_name" />
            <div>
              <strong>{{ detail.doctor.doctor_name }}</strong>
              <span>{{ detail.doctor.hospital_name || '未完善执业机构' }} · {{ detail.doctor.department || '未设置科室' }} · {{ detail.doctor.title_name || '未设置职称' }}</span>
            </div>
          </div>
          <div class="action-row" style="margin-top: 14px;">
            <StatusBadge :label="auditStatusLabel(detail.doctor.audit_status)" :tone="auditStatusTone(detail.doctor.audit_status)" />
            <StatusBadge :label="serviceStatusLabel(detail.doctor.service_status)" :tone="serviceStatusTone(detail.doctor.service_status)" />
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">资质与服务信息</div>
          <div class="key-value" style="margin-top: 10px;">
            <div class="key-value__row">
              <span>执业机构</span>
              <strong>{{ detail.doctor.hospital_name || '未完善' }}</strong>
            </div>
            <div class="key-value__row">
              <span>擅长方向</span>
              <strong>{{ splitVisibleText(detail.doctor.specialty).join('、') || '未完善' }}</strong>
            </div>
            <div class="key-value__row">
              <span>执业证号</span>
              <strong>{{ detail.doctor.license_no || '未填写' }}</strong>
            </div>
            <div class="key-value__row">
              <span>审核备注</span>
              <strong>{{ cleanVisibleText(detail.doctor.audit_remark, '暂无审核备注') }}</strong>
            </div>
          </div>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">处理能力统计</div>
          <div class="summary-grid summary-grid--three" style="margin-top: 12px;">
            <div><span>累计问诊</span><strong>{{ detail.stats.consultation_total }}</strong></div>
            <div><span>累计回复</span><strong>{{ detail.stats.reply_total }}</strong></div>
            <div><span>回复率</span><strong>{{ detail.stats.response_rate }}%</strong></div>
            <div><span>高风险病例</span><strong>{{ detail.stats.high_risk_total }}</strong></div>
          </div>
        </div>

        <div class="action-row" style="margin-top: 18px;">
          <button type="button" class="soft-button" @click="handleAudit(detail.doctor.doctor_id, 'APPROVED')">审核通过</button>
          <button type="button" class="ghost-button" @click="handleAudit(detail.doctor.doctor_id, 'REJECTED')">驳回审核</button>
          <button
            type="button"
            class="primary-button"
            @click="handleService(detail.doctor.doctor_id, detail.doctor.service_status === 1 ? 0 : 1)"
          >
            {{ detail.doctor.service_status === 1 ? '暂停服务' : '恢复服务' }}
          </button>
        </div>

        <div class="detail-card" style="margin-top: 18px;">
          <div class="tiny-label">最近处理咨询</div>
          <div v-if="detail.recent_consultations.length" class="list-panel" style="margin-top: 14px;">
            <article v-for="item in detail.recent_consultations" :key="item.case_id" class="list-row">
              <div class="list-row__head">
                <div>
                  <strong>{{ cleanVisibleText(item.summary_title, '图文问诊') }}</strong>
                  <span>{{ formatDateTime(item.submitted_at) }}</span>
                </div>
                <div class="action-row">
                  <StatusBadge :label="statusLabel(item.status)" :tone="statusTone(item.status)" />
                  <StatusBadge :label="riskLabel(item.risk_level)" :tone="riskTone(item.risk_level)" />
                </div>
              </div>
              <p class="list-row__summary">{{ cleanVisibleText(item.chief_complaint, '患者未补充更多主诉。') }}</p>
            </article>
          </div>
          <EmptyState v-else title="暂无处理记录" copy="该医生开始接诊后，这里会展示最近的处理咨询。" />
        </div>
      </div>
    </PanelCard>

    <PanelCard v-else title="暂无医生详情" subtitle="从左侧列表选择医生后，可查看完整资质和处理情况。">
      <EmptyState title="请选择医生" copy="点击左侧医生卡片，即可查看资质、审核备注与最近咨询记录。" />
    </PanelCard>
  </section>
</template>
