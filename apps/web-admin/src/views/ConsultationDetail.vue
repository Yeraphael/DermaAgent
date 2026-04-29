<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { client } from '@/api/client'

const route = useRoute()
const router = useRouter()
const caseId = Number(route.params.id)

const loading = ref(false)
const detail = ref<any>(null)
const messages = ref<any[]>([])
const replyForm = reactive({
  content: '',
  suggest_offline_visit: 0,
  suggest_follow_up: 1,
  doctor_remark: '',
})
const feedbackForm = reactive({
  ai_accuracy: 'MEDIUM',
  correction_note: '',
  knowledge_gap_note: '',
})

async function fetchDetail() {
  loading.value = true
  try {
    const [detailRes, msgRes] = await Promise.all([
      client.get(`/doctor/consultations/${caseId}`),
      client.get(`/consultations/${caseId}/messages`),
    ])
    detail.value = detailRes.data
    messages.value = msgRes.data
  } finally {
    loading.value = false
  }
}

async function submitReply() {
  try {
    await client.post(`/doctor/consultations/${caseId}/reply`, replyForm)
    ElMessage.success('医生回复已提交')
    replyForm.content = ''
    replyForm.doctor_remark = ''
    await fetchDetail()
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function submitFeedback() {
  try {
    await client.post(`/doctor/consultations/${caseId}/ai-feedback`, feedbackForm)
    ElMessage.success('AI 反馈已记录')
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

onMounted(fetchDetail)
</script>

<template>
  <div class="page-shell">
    <div class="glass-panel" style="padding: 24px;">
      <div class="section-head">
        <div>
          <h1 class="section-title">问诊详情</h1>
          <p class="section-subtitle">查看病例、患者档案、AI 结果，并提交医生回复。</p>
        </div>
        <div style="display: flex; gap: 10px;">
          <el-button plain @click="router.push('/doctor')">返回列表</el-button>
          <el-button v-if="detail?.patient" type="success" plain @click="router.push(`/doctor/patients/${detail.patient.user.account_id}`)">患者档案</el-button>
        </div>
      </div>

      <div v-if="detail" v-loading="loading" style="display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px;">
        <div style="display: flex; flex-direction: column; gap: 18px;">
          <el-card shadow="never">
            <template #header>
              <div class="section-head" style="margin-bottom: 0;">
                <div>
                  <strong>{{ detail.case_no }} · {{ detail.summary_title }}</strong>
                  <p class="section-subtitle" style="margin-top: 6px;">{{ detail.chief_complaint }}</p>
                </div>
                <el-tag :type="detail.risk_level === 'HIGH' ? 'danger' : detail.risk_level === 'MEDIUM' ? 'warning' : 'success'">{{ detail.risk_level }}</el-tag>
              </div>
            </template>
            <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px;">
              <div class="stat-card"><span class="stat-label">状态</span><strong style="font-size: 18px;">{{ detail.status }}</strong></div>
              <div class="stat-card"><span class="stat-label">瘙痒程度</span><strong style="font-size: 18px;">{{ detail.itch_level }}</strong></div>
              <div class="stat-card"><span class="stat-label">疼痛程度</span><strong style="font-size: 18px;">{{ detail.pain_level }}</strong></div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 16px;">
              <img
                v-for="image in detail.images"
                :key="image.image_id"
                :src="image.file_url"
                :alt="image.file_name"
                style="width: 100%; height: 180px; object-fit: cover; border-radius: 18px; border: 1px solid rgba(181, 216, 255, 0.12);"
              />
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header><strong>AI 图文辅助分析</strong></template>
            <div style="display: flex; flex-direction: column; gap: 12px;">
              <div><strong>图像观察：</strong>{{ detail.ai_result?.image_observation }}</div>
              <div><strong>可能方向：</strong>{{ detail.ai_result?.possible_conditions }}</div>
              <div><strong>护理建议：</strong>{{ detail.ai_result?.care_advice }}</div>
              <div><strong>就医提示：</strong>{{ detail.ai_result?.hospital_advice }}</div>
              <div style="color: var(--danger);"><strong>高风险提醒：</strong>{{ detail.ai_result?.high_risk_alert }}</div>
              <div style="color: var(--text-sub);">{{ detail.ai_result?.disclaimer }}</div>
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header><strong>沟通记录</strong></template>
            <div style="display: flex; flex-direction: column; gap: 12px; max-height: 280px; overflow: auto;">
              <div
                v-for="item in messages"
                :key="item.message_id"
                style="padding: 14px 16px; border-radius: 18px; background: rgba(9, 19, 34, 0.66); border: 1px solid rgba(181, 216, 255, 0.08);"
              >
                <div style="display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px;">
                  <strong>{{ item.sender_role }}</strong>
                  <span style="color: var(--text-sub);">{{ item.created_at }}</span>
                </div>
                <div>{{ item.content }}</div>
              </div>
            </div>
          </el-card>
        </div>

        <div style="display: flex; flex-direction: column; gap: 18px;">
          <el-card shadow="never">
            <template #header><strong>患者概览</strong></template>
            <div style="display: grid; gap: 10px;">
              <div><strong>姓名：</strong>{{ detail.patient?.profile?.real_name }}</div>
              <div><strong>城市：</strong>{{ detail.patient?.profile?.city }}</div>
              <div><strong>年龄：</strong>{{ detail.patient?.profile?.age }}</div>
              <div><strong>肤质：</strong>{{ detail.patient?.health_profile?.skin_type || '未填写' }}</div>
              <div><strong>过敏史：</strong>{{ detail.patient?.health_profile?.allergy_history || '未填写' }}</div>
              <div><strong>既往史：</strong>{{ detail.patient?.health_profile?.past_medical_history || '未填写' }}</div>
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header><strong>回复问诊</strong></template>
            <el-form label-position="top">
              <el-form-item label="医生建议">
                <el-input v-model="replyForm.content" type="textarea" :rows="5" placeholder="输入医生建议和复诊意见" />
              </el-form-item>
              <el-form-item label="医生备注">
                <el-input v-model="replyForm.doctor_remark" type="textarea" :rows="3" placeholder="记录补充说明或随访建议" />
              </el-form-item>
              <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                <el-switch v-model="replyForm.suggest_offline_visit" :active-value="1" :inactive-value="0" active-text="建议线下面诊" />
                <el-switch v-model="replyForm.suggest_follow_up" :active-value="1" :inactive-value="0" active-text="建议继续随访" />
              </div>
              <el-button class="accent-button" type="primary" @click="submitReply">提交回复</el-button>
            </el-form>
          </el-card>

          <el-card shadow="never">
            <template #header><strong>AI 纠偏反馈</strong></template>
            <el-form label-position="top">
              <el-form-item label="AI 准确度">
                <el-segmented
                  v-model="feedbackForm.ai_accuracy"
                  :options="[
                    { label: '高', value: 'HIGH' },
                    { label: '中', value: 'MEDIUM' },
                    { label: '低', value: 'LOW' },
                  ]"
                />
              </el-form-item>
              <el-form-item label="纠偏说明">
                <el-input v-model="feedbackForm.correction_note" type="textarea" :rows="3" placeholder="补充 AI 判断偏差和修正意见" />
              </el-form-item>
              <el-form-item label="知识缺口">
                <el-input v-model="feedbackForm.knowledge_gap_note" type="textarea" :rows="3" placeholder="补充后续模型或问答流程需要增强的方向" />
              </el-form-item>
              <el-button type="success" plain @click="submitFeedback">提交反馈</el-button>
            </el-form>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>
