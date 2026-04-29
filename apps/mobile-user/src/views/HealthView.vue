<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import PageState from '../components/PageState.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { deleteConsultation } from '../services/consultation'
import { fetchHealthArchive, type HealthArchiveResponse } from '../services/user'
import { formatDate, getRiskLabel, getRiskTone, guessSuggestionDetail, sanitizeVisibleText } from '../utils/display'

const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const archive = ref<HealthArchiveResponse | null>(null)
const deleteCaseId = ref<number | null>(null)
const deleteLoading = ref(false)
const expandedSuggestion = ref(0)

const statCards = computed(() => {
  if (!archive.value) return []
  return [
    {
      label: '皮肤类型',
      value: sanitizeVisibleText(archive.value.stats.skin_type, '未完善'),
      meta: archive.value.stats.skin_type_updated_at ? `更新于 ${archive.value.stats.skin_type_updated_at}` : '建议完善皮肤资料',
    },
    {
      label: '最近 30 天问诊',
      value: `${archive.value.stats.consultations_30d} 次`,
      meta: archive.value.stats.consultations_30d_delta ? `较上期 ${archive.value.stats.consultations_30d_delta > 0 ? '↑' : '↓'} ${Math.abs(archive.value.stats.consultations_30d_delta)}%` : '较上期 持平',
    },
    {
      label: '医生回复',
      value: `${archive.value.stats.doctor_replies_30d} 次`,
      meta: `累计 ${archive.value.stats.doctor_replies_total} 次`,
    },
    {
      label: '护理计划',
      value: sanitizeVisibleText(archive.value.stats.care_plan_status, '待建立'),
      meta: archive.value.stats.care_plan_updated_at ? `更新于 ${archive.value.stats.care_plan_updated_at}` : '待生成护理计划',
    },
  ]
})

async function loadArchive() {
  try {
    loading.value = true
    errorMessage.value = ''
    archive.value = await fetchHealthArchive()
  } catch (error) {
    archive.value = null
    errorMessage.value = (error as Error).message || '健康档案加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function confirmDeleteCase() {
  if (!deleteCaseId.value || !archive.value) return

  const backup = [...archive.value.recent_cases]
  archive.value = {
    ...archive.value,
    recent_cases: archive.value.recent_cases.filter((item) => item.case_id !== deleteCaseId.value),
  }

  try {
    deleteLoading.value = true
    await deleteConsultation(deleteCaseId.value)
    deleteCaseId.value = null
    window.alert('删除成功')
  } catch (error) {
    archive.value = {
      ...archive.value,
      recent_cases: backup,
    }
    window.alert((error as Error).message || '删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  void loadArchive()
})
</script>

<template>
  <section class="page-stack">
    <article class="surface-card">
      <p class="section-eyebrow">健康档案</p>
      <h1 class="section-title">记录您的皮肤健康信息与问诊历史，跟踪风险趋势，沉淀护理建议。</h1>
    </article>

    <PageState
      v-if="loading"
      title="正在加载健康档案"
      description="请稍候，我们正在整理您的健康概览与风险趋势。"
    />

    <PageState
      v-else-if="errorMessage"
      tone="error"
      title="健康档案加载失败"
      :description="errorMessage"
      action-text="重新加载"
      @action="loadArchive"
    />

    <PageState
      v-else-if="!archive"
      tone="empty"
      title="当前还没有可展示的健康档案"
      description="完成问诊并补充基础资料后，系统会在这里沉淀皮肤档案与护理建议。"
      action-text="去图文问诊"
      @action="router.push('/consultation')"
    />

    <template v-else>
      <div class="grid-2 health-stat-grid">
        <article v-for="item in statCards" :key="item.label" class="metric-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p class="meta-copy">{{ item.meta }}</p>
        </article>
      </div>

      <div class="grid-2">
        <article class="surface-card">
          <div class="section-head">
            <div>
              <p class="section-eyebrow">基础信息</p>
              <h2 class="card-title">当前档案</h2>
            </div>
            <button type="button" class="text-button" @click="router.push('/profile')">编辑资料</button>
          </div>

          <div class="health-info-grid">
            <div>
              <span>姓名</span>
              <strong>{{ sanitizeVisibleText(archive.basic_info.real_name, '未填写') }}</strong>
            </div>
            <div>
              <span>性别</span>
              <strong>{{ sanitizeVisibleText(archive.basic_info.gender, '未填写') }}</strong>
            </div>
            <div>
              <span>年龄</span>
              <strong>{{ archive.basic_info.age || '--' }}</strong>
            </div>
            <div>
              <span>手机号</span>
              <strong>{{ archive.basic_info.phone || '--' }}</strong>
            </div>
          </div>
        </article>

        <article class="surface-card">
          <div class="section-head">
            <div>
              <p class="section-eyebrow">风险趋势</p>
              <h2 class="card-title">近 90 天风险分布</h2>
            </div>
          </div>

          <div class="trend-list">
            <article v-for="item in archive.risk_trend" :key="item.level" class="trend-item">
              <div class="trend-item__head">
                <strong>{{ item.label }}</strong>
                <span>{{ item.percentage }}%</span>
              </div>
              <div class="trend-item__track">
                <span :style="{ width: `${item.percentage}%` }" :data-tone="getRiskTone(item.level)" />
              </div>
              <p>{{ item.days }} 天</p>
            </article>
          </div>
          <p class="meta-copy">风险评估基于问诊记录与皮肤状态分析，仅供参考。</p>
        </article>
      </div>

      <div class="grid-2">
        <article class="surface-card">
          <div class="section-head">
            <div>
              <p class="section-eyebrow">最近病例</p>
              <h2 class="card-title">近期记录</h2>
            </div>
          </div>

          <div class="case-list">
            <article v-for="item in archive.recent_cases" :key="item.case_id" class="case-item">
              <div>
                <strong>{{ sanitizeVisibleText(item.title, '皮肤健康记录') }}</strong>
                <p>{{ formatDate(item.submitted_at) }}</p>
              </div>
              <div class="case-item__actions">
                <RiskBadge :label="getRiskLabel(item.risk_level)" :tone="getRiskTone(item.risk_level)" />
                <button type="button" class="secondary-button" @click="router.push(`/analysis/${item.case_id}`)">查看详情</button>
                <button type="button" class="secondary-button" @click="deleteCaseId = item.case_id">删除</button>
              </div>
            </article>

            <p v-if="!archive.recent_cases.length" class="card-copy">当前暂无近期病例记录。</p>
          </div>
        </article>

        <article class="surface-card">
          <div class="section-head">
            <div>
              <p class="section-eyebrow">护理建议沉淀</p>
              <h2 class="card-title">长期建议</h2>
            </div>
          </div>

          <div class="suggestion-list">
            <article
              v-for="(item, index) in archive.care_suggestions"
              :key="item"
              class="suggestion-item"
            >
              <button type="button" class="suggestion-item__toggle" @click="expandedSuggestion = expandedSuggestion === index ? -1 : index">
                <strong>{{ sanitizeVisibleText(item) }}</strong>
                <span>{{ expandedSuggestion === index ? '收起' : '展开' }}</span>
              </button>
              <p v-if="expandedSuggestion === index">{{ guessSuggestionDetail(item) }}</p>
            </article>
          </div>
        </article>
      </div>
    </template>

    <ConfirmDialog
      :visible="deleteCaseId !== null"
      title="确认删除该记录？"
      description="删除后无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      :loading="deleteLoading"
      @cancel="deleteCaseId = null"
      @confirm="confirmDeleteCase"
    />
  </section>
</template>

<style scoped>
.health-stat-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.health-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.health-info-grid span {
  display: block;
  color: var(--text-faint);
  font-size: 12px;
}

.health-info-grid strong {
  display: block;
  margin-top: 6px;
  color: var(--text-strong);
  font-size: 16px;
}

.trend-list {
  display: grid;
  gap: 14px;
  margin: 14px 0;
}

.trend-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.trend-item__head strong {
  color: var(--text-strong);
  font-size: 14px;
}

.trend-item__head span,
.trend-item p {
  color: var(--text-sub);
  font-size: 13px;
}

.trend-item p {
  margin: 8px 0 0;
}

.trend-item__track {
  margin-top: 8px;
  height: 10px;
  border-radius: 999px;
  background: rgba(226, 233, 247, 0.92);
  overflow: hidden;
}

.trend-item__track span {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.trend-item__track span[data-tone='mint'] {
  background: linear-gradient(90deg, rgba(24, 184, 141, 0.85), rgba(48, 211, 170, 0.85));
}

.trend-item__track span[data-tone='amber'] {
  background: linear-gradient(90deg, rgba(242, 156, 56, 0.85), rgba(255, 194, 95, 0.85));
}

.trend-item__track span[data-tone='rose'] {
  background: linear-gradient(90deg, rgba(239, 91, 109, 0.85), rgba(255, 133, 112, 0.85));
}

.case-list,
.suggestion-list {
  display: grid;
  gap: 12px;
}

.case-item,
.suggestion-item {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(248, 250, 255, 0.98);
}

.case-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.case-item strong,
.suggestion-item strong {
  color: var(--text-strong);
  font-size: 15px;
}

.case-item p {
  margin: 8px 0 0;
  color: var(--text-sub);
  font-size: 13px;
}

.case-item__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.suggestion-item__toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 0;
  background: transparent;
  padding: 0;
}

.suggestion-item__toggle span {
  color: var(--blue);
  font-size: 13px;
  font-weight: 700;
}

.suggestion-item p {
  margin: 12px 0 0;
  color: var(--text-sub);
  font-size: 14px;
  line-height: 1.8;
}

@media (max-width: 980px) {
  .health-stat-grid,
  .health-info-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .case-item {
    align-items: stretch;
    flex-direction: column;
  }

  .case-item__actions {
    justify-content: flex-start;
  }
}
</style>
