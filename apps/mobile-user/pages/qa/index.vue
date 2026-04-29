<script setup lang="ts">
import { onLoad, onShow } from '@dcloudio/uni-app'
import { computed, nextTick, reactive, ref } from 'vue'

import { createChatSession, deleteChatSession, fetchChatMessages, fetchChatSessions, sendChatMessage, type ChatMessage, type ChatSessionSummary } from '../../services/chat'
import { formatDateTime, sanitizeVisibleText } from '../../utils/display'
import { ensureLogin } from '../../utils/api'

const quickPrompts = [
  '湿疹和过敏有什么区别？',
  '湿疹可以根治吗？',
  '湿疹饮食上要注意什么？',
  '宝宝湿疹护理要点有哪些？',
]

const sessions = ref<ChatSessionSummary[]>([])
const messages = ref<ChatMessage[]>([])
const activeSessionId = ref<number | null>(null)
const activeSessionTitle = ref('知识问答')
const loading = ref(false)
const sending = ref(false)
const statusText = ref('')
const composer = reactive({
  message: '',
})
const drawerOpen = ref(false)
const manageMode = ref(false)
const selectedIds = ref<number[]>([])
const scrollIntoView = ref('')
const pendingAsk = ref('')

const isEmpty = computed(() => !messages.value.length)
const allSelected = computed(() => sessions.value.length > 0 && selectedIds.value.length === sessions.value.length)

function toast(title: string) {
  uni.showToast({ title, icon: 'none' })
}

function getMessageId(message: ChatMessage) {
  return `msg-${message.message_id}`
}

async function scrollToBottom() {
  await nextTick()
  const last = messages.value[messages.value.length - 1]
  scrollIntoView.value = last ? getMessageId(last) : ''
}

function sessionTitle(title?: string | null) {
  return sanitizeVisibleText(title, '新的对话')
}

async function openSession(sessionId: number) {
  loading.value = true
  try {
    const detail = await fetchChatMessages(sessionId)
    activeSessionId.value = detail.session_id
    activeSessionTitle.value = sessionTitle(detail.title)
    messages.value = detail.messages || []
    drawerOpen.value = false
    await scrollToBottom()
  } catch (error: any) {
    toast(error.message || '会话加载失败')
  } finally {
    loading.value = false
  }
}

async function ensureSession(preferredSessionId?: number) {
  const data = await fetchChatSessions()
  sessions.value = data.items || []

  if (!sessions.value.length) {
    const created = await createChatSession()
    sessions.value = [
      {
        session_id: created.session_id,
        title: created.title,
        last_message: null,
        updated_at: created.created_at,
      },
    ]
  }

  const targetId = preferredSessionId || activeSessionId.value || sessions.value[0]?.session_id || null
  if (targetId) {
    await openSession(targetId)
  }
}

async function createNewConversation() {
  try {
    const created = await createChatSession()
    sessions.value = [
      {
        session_id: created.session_id,
        title: created.title,
        last_message: null,
        updated_at: created.created_at,
      },
      ...sessions.value,
    ]
    activeSessionId.value = created.session_id
    activeSessionTitle.value = sessionTitle(created.title)
    messages.value = []
    composer.message = ''
    drawerOpen.value = false
    manageMode.value = false
    selectedIds.value = []
  } catch (error: any) {
    toast(error.message || '新建对话失败')
  }
}

function inferStatusText(text: string) {
  if (/指南|现在|最新|医院|药品/.test(text)) {
    return '正在整理相关参考信息...'
  }
  if (/发热|渗液|脓疱|疼痛|加重/.test(text)) {
    return '正在优先生成风险提醒...'
  }
  return '正在生成回答，请稍候...'
}

async function sendMessage() {
  const message = composer.message.trim()
  if (!message || sending.value) return

  if (!activeSessionId.value) {
    await ensureSession()
  }
  if (!activeSessionId.value) {
    toast('当前会话初始化失败')
    return
  }

  const optimisticMessage: ChatMessage = {
    message_id: Date.now(),
    role: 'user',
    content: message,
    intent: null,
    used_tool: false,
    tool_name: null,
    sources: [],
    model_name: null,
    created_at: '刚刚',
  }

  composer.message = ''
  sending.value = true
  statusText.value = '正在准备回答...'
  messages.value = [...messages.value, optimisticMessage]
  await scrollToBottom()

  const timer = setTimeout(() => {
    statusText.value = inferStatusText(message)
  }, 400)

  try {
    await sendChatMessage(activeSessionId.value, message)
    await openSession(activeSessionId.value)
    const data = await fetchChatSessions()
    sessions.value = data.items || sessions.value
  } catch (error: any) {
    composer.message = message
    toast(error.message || '发送失败，请稍后重试')
  } finally {
    clearTimeout(timer)
    sending.value = false
    statusText.value = ''
  }
}

function toggleSelect(id: number) {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((item) => item !== id)
    return
  }
  selectedIds.value = [...selectedIds.value, id]
}

function toggleSelectAll() {
  selectedIds.value = allSelected.value ? [] : sessions.value.map((item) => item.session_id)
}

function askPrompt(prompt: string) {
  composer.message = prompt
}

function confirmDelete(ids: number[]) {
  const content = ids.length > 1 ? '确认删除选中的会话？删除后无法恢复。' : '确认删除该会话？删除后无法恢复。'
  uni.showModal({
    title: '删除确认',
    content,
    success: async (res) => {
      if (!res.confirm) return

      const backupSessions = [...sessions.value]
      const backupMessages = [...messages.value]
      const backupActiveId = activeSessionId.value
      const nextSessions = sessions.value.filter((item) => !ids.includes(item.session_id))
      sessions.value = nextSessions
      selectedIds.value = []
      manageMode.value = false

      try {
        await Promise.all(ids.map((id) => deleteChatSession(id)))
        if (backupActiveId && ids.includes(backupActiveId)) {
          if (nextSessions[0]) {
            await openSession(nextSessions[0].session_id)
          } else {
            await createNewConversation()
          }
        }
        uni.showToast({ title: '删除成功', icon: 'success' })
      } catch (error: any) {
        sessions.value = backupSessions
        messages.value = backupMessages
        activeSessionId.value = backupActiveId
        toast(error.message || '删除失败，请稍后重试')
      }
    },
  })
}

async function initialize(preferred?: number) {
  if (!ensureLogin()) return
  await ensureSession(preferred)
  if (pendingAsk.value) {
    composer.message = pendingAsk.value
    pendingAsk.value = ''
    await sendMessage()
  }
}

onLoad((options) => {
  pendingAsk.value = sanitizeVisibleText(options?.ask || '')
})

onShow(() => {
  const storedAsk = sanitizeVisibleText(uni.getStorageSync('qa_pending_ask'))
  const storedSession = Number(uni.getStorageSync('qa_target_session') || 0) || undefined
  if (storedAsk) {
    pendingAsk.value = storedAsk
    uni.removeStorageSync('qa_pending_ask')
  }
  if (storedSession) {
    uni.removeStorageSync('qa_target_session')
  }
  const preferred = storedSession || Number((getCurrentPages().slice(-1)[0] as any)?.options?.session || 0) || undefined
  void initialize(preferred)
})
</script>

<template>
  <view class="page-wrap safe-top qa-page">
    <view class="surface-card qa-header">
      <view class="qa-header__row">
        <view class="secondary-btn qa-header__menu" @click="drawerOpen = true">会话列表</view>
        <view>
          <view class="section-title">知识问答</view>
          <view class="section-subtitle">围绕皮肤问题进行连续问答，获得日常护理与就医参考。</view>
        </view>
      </view>
    </view>

    <view v-if="drawerOpen" class="qa-drawer-mask" @click="drawerOpen = false" />
    <view class="surface-card qa-drawer" :class="{ open: drawerOpen }">
      <view class="qa-drawer__actions">
        <view class="primary-btn" @click="createNewConversation">新建对话</view>
        <view class="secondary-btn" @click="manageMode = !manageMode; selectedIds = []">
          {{ manageMode ? '取消管理' : '批量管理' }}
        </view>
      </view>

      <view v-if="manageMode" class="qa-batch">
        <view class="text-btn" @click="toggleSelectAll">{{ allSelected ? '取消全选' : '全选' }}</view>
        <view class="label">已选 {{ selectedIds.length }} 项</view>
        <view class="text-btn qa-batch__danger" @click="selectedIds.length && confirmDelete(selectedIds)">删除所选</view>
      </view>

      <scroll-view scroll-y class="qa-drawer__list">
        <view v-for="session in sessions" :key="session.session_id" class="qa-drawer__item" :class="{ active: activeSessionId === session.session_id }">
          <view v-if="manageMode" class="qa-drawer__check" @click="toggleSelect(session.session_id)">
            {{ selectedIds.includes(session.session_id) ? '✓' : '' }}
          </view>
          <view class="qa-drawer__main" @click="openSession(session.session_id)">
            <view class="qa-drawer__title">{{ sessionTitle(session.title) }}</view>
            <view class="qa-drawer__time">{{ formatDateTime(session.updated_at) }}</view>
          </view>
          <view v-if="!manageMode" class="text-btn" @click="confirmDelete([session.session_id])">删除</view>
        </view>
      </scroll-view>
    </view>

    <view class="surface-card qa-content">
      <view class="section-subtitle" style="margin-top: 0;">{{ activeSessionTitle }}</view>
      <view class="chip-row" style="margin-top: 18rpx;">
        <view v-for="prompt in quickPrompts" :key="prompt" class="chip" @click="askPrompt(prompt)">{{ prompt }}</view>
      </view>

      <view v-if="loading" class="qa-empty">
        <view class="section-subtitle">正在加载会话内容...</view>
      </view>

      <view v-else-if="isEmpty" class="qa-empty">
        <view class="section-subtitle">点击推荐问题开始对话，或在下方输入框直接提问。</view>
      </view>

      <scroll-view v-else scroll-y class="qa-thread" :scroll-into-view="scrollIntoView">
        <view
          v-for="message in messages"
          :id="getMessageId(message)"
          :key="message.message_id"
          class="qa-bubble-wrap"
          :class="{ user: message.role === 'user' }"
        >
          <view class="qa-meta">{{ message.role === 'user' ? '用户' : '智能助手' }}｜{{ formatDateTime(message.created_at) }}</view>
          <view class="qa-bubble" :class="{ user: message.role === 'user' }">
            <text class="qa-bubble__text">{{ sanitizeVisibleText(message.content) }}</text>
          </view>
        </view>

        <view v-if="sending" class="qa-bubble-wrap">
          <view class="qa-meta">智能助手｜正在生成</view>
          <view class="qa-bubble">
            <text class="qa-bubble__text">{{ statusText }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="surface-card qa-composer">
      <textarea v-model="composer.message" class="textarea-box" maxlength="2000" placeholder="请输入你的问题" />
      <view class="qa-composer__footer">
        <view class="section-subtitle qa-composer__hint">内容由智能助手生成，仅供参考，不能替代专业医疗建议。</view>
        <view class="primary-btn" @click="sendMessage">{{ sending ? '发送中...' : '发送' }}</view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.qa-page {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.qa-header,
.qa-content,
.qa-composer,
.qa-drawer {
  padding: 28rpx;
}

.qa-header__row {
  display: flex;
  gap: 16rpx;
}

.qa-header__menu {
  width: 180rpx;
  flex-shrink: 0;
}

.qa-drawer-mask {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: rgba(17, 31, 55, 0.28);
}

.qa-drawer {
  position: fixed;
  top: 24rpx;
  left: 24rpx;
  bottom: 24rpx;
  z-index: 35;
  width: 620rpx;
  transform: translateX(-110%);
  transition: transform 0.22s ease;
}

.qa-drawer.open {
  transform: translateX(0);
}

.qa-drawer__actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.qa-batch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 24rpx;
  background: rgba(248, 250, 255, 0.98);
}

.qa-batch__danger {
  color: #ef5b6d;
}

.qa-drawer__list {
  height: calc(100% - 170rpx);
  margin-top: 18rpx;
}

.qa-drawer__item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12rpx;
  align-items: center;
  padding: 20rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 24rpx;
  background: rgba(248, 250, 255, 0.98);
}

.qa-drawer__item + .qa-drawer__item {
  margin-top: 12rpx;
}

.qa-drawer__item.active {
  border-color: rgba(47, 125, 255, 0.46);
}

.qa-drawer__check {
  width: 44rpx;
  height: 44rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(47, 125, 255, 0.46);
  color: #2f7dff;
}

.qa-drawer__title {
  color: #15326a;
  font-size: 28rpx;
  font-weight: 700;
}

.qa-drawer__time {
  margin-top: 8rpx;
  color: #7a8fb3;
  font-size: 22rpx;
}

.qa-empty {
  min-height: 260rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qa-thread {
  max-height: 780rpx;
  margin-top: 20rpx;
}

.qa-bubble-wrap + .qa-bubble-wrap {
  margin-top: 18rpx;
}

.qa-bubble-wrap.user {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.qa-meta {
  color: #7a8fb3;
  font-size: 22rpx;
}

.qa-bubble {
  margin-top: 10rpx;
  padding: 22rpx;
  border: 1px solid rgba(166, 187, 224, 0.42);
  border-radius: 28rpx;
  background: rgba(248, 250, 255, 0.98);
}

.qa-bubble.user {
  background: linear-gradient(135deg, #2879ff, #5097ff 42%, #1cc9c2);
  border-color: transparent;
}

.qa-bubble__text {
  color: #17345f;
  font-size: 28rpx;
  line-height: 1.9;
  white-space: pre-wrap;
}

.qa-bubble.user .qa-bubble__text {
  color: #ffffff;
}

.qa-composer__footer {
  margin-top: 18rpx;
}

.qa-composer__hint {
  margin-bottom: 14rpx;
}
</style>
