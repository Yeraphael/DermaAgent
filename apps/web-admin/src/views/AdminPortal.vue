<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { client } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const activeTab = ref('dashboard')
const loading = ref(false)
const overview = ref<any>({})
const users = ref<any[]>([])
const doctors = ref<any[]>([])
const consultations = ref<any[]>([])
const documents = ref<any[]>([])
const configs = ref<any[]>([])
const operationLogs = ref<any[]>([])
const modelLogs = ref<any[]>([])
const trends = ref<any[]>([])
const hotQuestions = ref<any[]>([])
const knowledgeForm = reactive({
  title: '',
  category: '皮肤疾病',
  tag_list: '保湿,屏障,护理',
  summary: '',
})

async function fetchAll() {
  loading.value = true
  try {
    const responses = await Promise.all([
      client.get('/admin/stats/overview'),
      client.get('/admin/users', { params: { page: 1, page_size: 50 } }),
      client.get('/admin/doctors', { params: { page: 1, page_size: 50 } }),
      client.get('/admin/consultations', { params: { page: 1, page_size: 50 } }),
      client.get('/admin/knowledge/documents', { params: { page: 1, page_size: 50 } }),
      client.get('/admin/configs'),
      client.get('/admin/logs/operations', { params: { page: 1, page_size: 40 } }),
      client.get('/admin/logs/model-calls'),
      client.get('/admin/stats/consultation-trend'),
      client.get('/admin/stats/hot-questions'),
    ])
    overview.value = responses[0].data
    users.value = responses[1].data.list
    doctors.value = responses[2].data.list
    consultations.value = responses[3].data.list
    documents.value = responses[4].data.list
    configs.value = responses[5].data
    operationLogs.value = responses[6].data.list
    modelLogs.value = responses[7].data
    trends.value = responses[8].data
    hotQuestions.value = responses[9].data
  } finally {
    loading.value = false
  }
}

async function updateUserStatus(row: any, status: number) {
  await client.put(`/admin/users/${row.account.account_id}/status`, { status })
  ElMessage.success('用户状态已更新')
  await fetchAll()
}

async function auditDoctor(row: any, audit_status: string) {
  await client.put(`/admin/doctors/${row.doctor_id}/audit`, {
    audit_status,
    audit_remark: audit_status === 'APPROVED' ? '资质审核通过，可进入接诊状态' : '请补充完整资质材料',
  })
  ElMessage.success('医生审核已更新')
  await fetchAll()
}

async function toggleDoctorService(row: any) {
  await client.put(`/admin/doctors/${row.doctor_id}/status`, { status: row.service_status === 1 ? 0 : 1 })
  ElMessage.success('医生服务状态已更新')
  await fetchAll()
}

async function closeConsultation(row: any) {
  await client.post(`/admin/consultations/${row.case_id}/close`)
  ElMessage.success('问诊单已关闭')
  await fetchAll()
}

async function createKnowledge() {
  const form = new FormData()
  form.append('title', knowledgeForm.title)
  form.append('category', knowledgeForm.category)
  form.append('tag_list', knowledgeForm.tag_list)
  form.append('summary', knowledgeForm.summary)
  await client.post('/admin/knowledge/documents/upload', form)
  ElMessage.success('知识文档已创建')
  knowledgeForm.title = ''
  knowledgeForm.summary = ''
  await fetchAll()
}

async function processDocument(documentId: number, action: 'parse' | 'chunk' | 'embed') {
  await client.post(`/admin/knowledge/documents/${documentId}/${action}`)
  ElMessage.success(`文档已执行 ${action}`)
  await fetchAll()
}

async function toggleDocument(row: any) {
  await client.put(`/admin/knowledge/documents/${row.document_id}/status`, {
    enabled_flag: row.enabled_flag === 1 ? 0 : 1,
  })
  ElMessage.success('知识库状态已更新')
  await fetchAll()
}

async function saveConfig(row: any) {
  await client.put(`/admin/configs/${row.config_key}`, { config_value: row.config_value })
  ElMessage.success('配置已保存')
}

function logout() {
  auth.logout()
  router.replace('/login')
}

onMounted(async () => {
  try {
    await fetchAll()
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
})
</script>

<template>
  <div class="page-shell">
    <div class="glass-panel" style="padding: 26px;">
      <div class="section-head">
        <div>
          <h1 class="section-title">管理员控制台</h1>
          <p class="section-subtitle">统一管理用户、医生、问诊流程、知识库、系统配置与运行日志。</p>
        </div>
        <div style="display: flex; gap: 10px;">
          <el-tag type="success" size="large">{{ auth.account?.username }} · 管理员</el-tag>
          <el-button plain @click="logout">退出</el-button>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card"><span class="stat-label">用户总量</span><strong>{{ overview.users_total || 0 }}</strong></div>
        <div class="stat-card"><span class="stat-label">医生总量</span><strong>{{ overview.doctors_total || 0 }}</strong></div>
        <div class="stat-card"><span class="stat-label">问诊总量</span><strong>{{ overview.consultations_total || 0 }}</strong></div>
        <div class="stat-card"><span class="stat-label">高风险问诊</span><strong>{{ overview.high_risk_total || 0 }}</strong></div>
      </div>
    </div>

    <div style="height: 18px;" />

    <div class="glass-panel" style="padding: 22px;" v-loading="loading">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="控制台" name="dashboard">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 18px;">
            <el-card shadow="never">
              <template #header><strong>热点问题</strong></template>
              <el-table :data="hotQuestions">
                <el-table-column prop="question" label="问题" min-width="220" />
                <el-table-column prop="count" label="次数" width="100" />
                <el-table-column prop="latest_time" label="最近出现" width="180" />
              </el-table>
            </el-card>
            <el-card shadow="never">
              <template #header><strong>趋势快照</strong></template>
              <el-table :data="trends.slice(-12)">
                <el-table-column prop="snapshot_date" label="日期" width="120" />
                <el-table-column prop="metric_key" label="指标" width="170" />
                <el-table-column prop="metric_value" label="值" width="100" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="用户管理" name="users">
          <el-table :data="users" height="560">
            <el-table-column label="账号" min-width="140">
              <template #default="{ row }">{{ row.account.username }}</template>
            </el-table-column>
            <el-table-column label="姓名" min-width="120">
              <template #default="{ row }">{{ row.profile.real_name }}</template>
            </el-table-column>
            <el-table-column label="城市" min-width="100">
              <template #default="{ row }">{{ row.profile.city }}</template>
            </el-table-column>
            <el-table-column label="手机号" min-width="140">
              <template #default="{ row }">{{ row.account.phone }}</template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="row.account.status === 1 ? 'success' : 'danger'">{{ row.account.status === 1 ? '正常' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="180" fixed="right">
              <template #default="{ row }">
                <div style="display: flex; gap: 8px;">
                  <el-button size="small" type="success" plain @click="updateUserStatus(row, 1)">启用</el-button>
                  <el-button size="small" type="danger" plain @click="updateUserStatus(row, 0)">停用</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="医生管理" name="doctors">
          <el-table :data="doctors" height="560">
            <el-table-column prop="doctor_name" label="医生" min-width="130" />
            <el-table-column prop="department" label="科室" width="120" />
            <el-table-column prop="hospital_name" label="机构" min-width="220" />
            <el-table-column prop="title_name" label="职称" width="120" />
            <el-table-column prop="audit_status" label="审核" width="120" />
            <el-table-column prop="service_status" label="服务状态" width="120">
              <template #default="{ row }">{{ row.service_status === 1 ? '在线' : '停用' }}</template>
            </el-table-column>
            <el-table-column label="操作" min-width="260" fixed="right">
              <template #default="{ row }">
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                  <el-button size="small" type="success" plain @click="auditDoctor(row, 'APPROVED')">通过</el-button>
                  <el-button size="small" type="warning" plain @click="auditDoctor(row, 'PENDING')">待补充</el-button>
                  <el-button size="small" type="danger" plain @click="auditDoctor(row, 'REJECTED')">驳回</el-button>
                  <el-button size="small" @click="toggleDoctorService(row)">{{ row.service_status === 1 ? '暂停服务' : '恢复服务' }}</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="问诊管理" name="consultations">
          <el-table :data="consultations" height="560">
            <el-table-column prop="case_no" label="病例号" min-width="150" />
            <el-table-column prop="summary_title" label="摘要" min-width="180" />
            <el-table-column label="患者" min-width="120">
              <template #default="{ row }">{{ row.patient.profile.real_name }}</template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险" width="110" />
            <el-table-column prop="status" label="状态" width="140" />
            <el-table-column label="医生" min-width="120">
              <template #default="{ row }">{{ row.doctor?.doctor_name || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="danger" plain @click="closeConsultation(row)">关闭</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="知识库管理" name="knowledge">
          <div style="display: grid; grid-template-columns: 360px 1fr; gap: 18px;">
            <el-card shadow="never">
              <template #header><strong>新建知识文档</strong></template>
              <el-form label-position="top">
                <el-form-item label="标题">
                  <el-input v-model="knowledgeForm.title" placeholder="例如：湿疹家庭护理建议" />
                </el-form-item>
                <el-form-item label="分类">
                  <el-input v-model="knowledgeForm.category" />
                </el-form-item>
                <el-form-item label="标签">
                  <el-input v-model="knowledgeForm.tag_list" />
                </el-form-item>
                <el-form-item label="摘要">
                  <el-input v-model="knowledgeForm.summary" type="textarea" :rows="4" />
                </el-form-item>
                <el-button class="accent-button" type="primary" @click="createKnowledge">创建文档</el-button>
              </el-form>
            </el-card>

            <el-card shadow="never">
              <template #header><strong>文档列表</strong></template>
              <el-table :data="documents" height="540">
                <el-table-column prop="doc_title" label="标题" min-width="220" />
                <el-table-column prop="category" label="分类" width="120" />
                <el-table-column prop="parse_status" label="状态" width="120" />
                <el-table-column prop="chunk_count" label="分块数" width="100" />
                <el-table-column prop="enabled_flag" label="启用" width="90">
                  <template #default="{ row }">{{ row.enabled_flag === 1 ? '是' : '否' }}</template>
                </el-table-column>
                <el-table-column label="操作" min-width="270">
                  <template #default="{ row }">
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                      <el-button size="small" @click="processDocument(row.document_id, 'parse')">解析</el-button>
                      <el-button size="small" @click="processDocument(row.document_id, 'chunk')">切分</el-button>
                      <el-button size="small" type="success" plain @click="processDocument(row.document_id, 'embed')">嵌入</el-button>
                      <el-button size="small" type="warning" plain @click="toggleDocument(row)">{{ row.enabled_flag === 1 ? '停用' : '启用' }}</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="系统配置" name="configs">
          <el-table :data="configs" height="560">
            <el-table-column prop="config_key" label="配置键" min-width="220" />
            <el-table-column prop="config_group" label="分组" width="120" />
            <el-table-column label="配置值" min-width="300">
              <template #default="{ row }">
                <el-input v-model="row.config_value" />
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="180" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="success" plain @click="saveConfig(row)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="日志与统计" name="logs">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 18px;">
            <el-card shadow="never">
              <template #header><strong>操作日志</strong></template>
              <el-table :data="operationLogs" height="520">
                <el-table-column prop="module_name" label="模块" width="110" />
                <el-table-column prop="operation_type" label="操作" width="130" />
                <el-table-column prop="operation_desc" label="说明" min-width="220" />
                <el-table-column prop="role_type" label="角色" width="100" />
                <el-table-column prop="operation_result" label="结果" width="100" />
                <el-table-column prop="created_at" label="时间" width="180" />
              </el-table>
            </el-card>
            <el-card shadow="never">
              <template #header><strong>模型调用记录</strong></template>
              <el-table :data="modelLogs" height="520">
                <el-table-column prop="biz_type" label="类型" width="120" />
                <el-table-column prop="model_name" label="模型" width="140" />
                <el-table-column prop="status" label="状态" width="100" />
                <el-table-column prop="summary" label="摘要" min-width="220" />
                <el-table-column prop="created_at" label="时间" width="180" />
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>
