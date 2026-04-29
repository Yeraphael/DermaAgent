<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ConfirmDialog from '../components/ConfirmDialog.vue'
import PageState from '../components/PageState.vue'
import {
  createChatSession,
  deleteChatSession,
  fetchChatMessages,
  fetchChatSessions,
  sendChatMessage,
  type ChatMessage,
  type ChatSessionSummary,
  type ChatSource,
} from '../services/chat'
import { formatDateTime, sanitizeVisibleText } from '../utils/display'

const markdown = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  typographer: false,
})

const defaultLinkRenderer =
  markdown.renderer.rules.link_open ??
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

markdown.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkRenderer(tokens, idx, options, env, self)
}

const route = useRoute()
const router = useRouter()

const quickQuestions = [
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
const refreshing = ref(false)
const sending = ref(false)
const loadError = ref('')
const statusText = ref('')
const drawerOpen = ref(false)
const manageMode = ref(false)
const selectedSessionIds = ref<number[]>([])
const deleteTargetId = ref<number | null>(null)
const batchDeleteDialogOpen = ref(false)
const deleteLoading = ref(false)
const composer = reactive({
  message: '',
})
const chatScrollRef = ref<HTMLDivElement | null>(null)
const appliedAsk = ref('')

const isEmpty = computed(() => !messages.value.length)
const allSessionsSelected = computed(() => sessions.value.length > 0 && selectedSessionIds.value.length === sessions.value.length)

function renderMarkdown(content: string) {
  return markdown.render(sanitizeVisibleText(content))
}

function sessionTitle(session: ChatSessionSummary) {
  return sanitizeVisibleText(session.title, '新的对话')
}

function messageText(content: string) {
  return sanitizeVisibleText(content)
}

function sourceTitle(source: ChatSource, index: number) {
  return sanitizeVisibleText(source.title, `参考来源 ${index + 1}`)
}

function normalizeUrl(url: string) {
  return /^https?:\/\//i.test(url) ? url : ''
}

function toggleDrawer(force?: boolean) {
  drawerOpen.value = typeof force === 'boolean' ? force : !drawerOpen.value
}

function toggleManageMode() {
  manageMode.value = !manageMode.value
  selectedSessionIds.value = []
}

function toggleSelection(sessionId: number) {
  if (selectedSessionIds.value.includes(sessionId)) {
    selectedSessionIds.value = selectedSessionIds.value.filter((id) => id !== sessionId)
    return
  }
  selectedSessionIds.value = [...selectedSessionIds.value, sessionId]
}

function toggleSelectAll() {
  selectedSessionIds.value = allSessionsSelected.value ? [] : sessions.value.map((item) => item.session_id)
}

async function scrollToBottom() {
  await nextTick()
  const node = chatScrollRef.value
  if (node) {
    node.scrollTop = node.scrollHeight
  }
}

async function openSession(sessionId: number, options: { quiet?: boolean } = {}) {
  loadError.value = ''
  if (options.quiet) {
    refreshing.value = true
  } else {
    loading.value = true
  }

  try {
    const detail = await fetchChatMessages(sessionId)
    activeSessionId.value = detail.session_id
    activeSessionTitle.value = sanitizeVisibleText(detail.title, '知识问答')
    messages.value = detail.messages || []
    drawerOpen.value = false
    await scrollToBottom()
  } catch (error) {
    loadError.value = (error as Error).message || '会话加载失败，请稍后重试。'
    if (!options.quiet) {
      messages.value = []
    }
  } finally {
    refreshing.value = false
    loading.value = false
  }
}

async function ensureSessions(preferredSessionId?: number) {
  loadError.value = ''
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
  if (!targetId) return
  await openSession(targetId, { quiet: preferredSessionId === activeSessionId.value })
}

async function initialize() {
  try {
    const preferred = Number(route.query.session || 0) || undefined
    await ensureSessions(preferred)

    const ask = sanitizeVisibleText(route.query.ask)
    if (ask && ask !== appliedAsk.value) {
      appliedAsk.value = ask
      composer.message = ask
      await sendMessage()
    }
  } catch (error) {
    loadError.value = (error as Error).message || '会话初始化失败，请稍后重试。'
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
    messages.value = []
    activeSessionId.value = created.session_id
    activeSessionTitle.value = sanitizeVisibleText(created.title, '新的对话')
    composer.message = ''
    drawerOpen.value = false
    manageMode.value = false
    selectedSessionIds.value = []
  } catch (error) {
    window.alert((error as Error).message || '新建对话失败，请稍后重试。')
  }
}

function inferStatusText(text: string) {
  if (/[最新|现在|指南|政策|医院|药品]/.test(text)) {
    return '正在整理与问题相关的参考信息...'
  }
  if (/发热|渗液|脓疱|疼痛|加重/.test(text)) {
    return '正在优先生成风险提醒...'
  }
  return '正在生成回答，请稍候...'
}

async function sendMessage() {
  const message = composer.message.trim()
  if (!message || sending.value) {
    return
  }

  if (!activeSessionId.value) {
    await ensureSessions()
  }
  if (!activeSessionId.value) {
    window.alert('当前会话初始化失败，请稍后重试。')
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

  const timer = window.setTimeout(() => {
    statusText.value = inferStatusText(message)
  }, 400)

  try {
    await sendChatMessage(activeSessionId.value, message)
    await openSession(activeSessionId.value, { quiet: true })
    const latestSessions = await fetchChatSessions()
    sessions.value = latestSessions.items || sessions.value
  } catch (error) {
    composer.message = message
    await openSession(activeSessionId.value, { quiet: true })
    window.alert((error as Error).message || '发送失败，请稍后重试。')
  } finally {
    window.clearTimeout(timer)
    sending.value = false
    statusText.value = ''
  }
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void sendMessage()
  }
}

function askPrompt(prompt: string) {
  composer.message = prompt
}

function askPromptAndSend(prompt: string) {
  composer.message = prompt
  void sendMessage()
}

function requestDeleteSession(sessionId: number) {
  deleteTargetId.value = sessionId
}

async function handleDelete(sessionIds: number[]) {
  const backupSessions = [...sessions.value]
  const backupMessages = [...messages.value]
  const backupActiveId = activeSessionId.value
  const nextSessions = sessions.value.filter((item) => !sessionIds.includes(item.session_id))

  sessions.value = nextSessions
  selectedSessionIds.value = []
  manageMode.value = false
  drawerOpen.value = false

  const nextActiveId = nextSessions[0]?.session_id || null
  if (backupActiveId && sessionIds.includes(backupActiveId)) {
    activeSessionId.value = nextActiveId
    messages.value = []
    activeSessionTitle.value = nextSessions[0] ? sessionTitle(nextSessions[0]) : '知识问答'
  }

  try {
    deleteLoading.value = true
    await Promise.all(sessionIds.map((id) => deleteChatSession(id)))

    if (activeSessionId.value && !sessionIds.includes(activeSessionId.value)) {
      await openSession(activeSessionId.value, { quiet: true })
    } else if (nextActiveId) {
      await openSession(nextActiveId, { quiet: true })
    } else {
      await createNewConversation()
    }

    window.alert('删除成功')
  } catch (error) {
    sessions.value = backupSessions
    messages.value = backupMessages
    activeSessionId.value = backupActiveId
    activeSessionTitle.value = backupSessions.find((item) => item.session_id === backupActiveId)?.title || '知识问答'
    window.alert((error as Error).message || '删除失败，请稍后重试')
  } finally {
    deleteLoading.value = false
    deleteTargetId.value = null
    batchDeleteDialogOpen.value = false
  }
}

watch(
  () => route.fullPath,
  () => {
    void initialize()
  },
)

onMounted(() => {
  void initialize()
})
</script>

<template>
  <section class="page-stack">
    <article class="surface-card qa-banner">
      <div class="qa-banner__row">
        <button type="button" class="secondary-button qa-menu-button" @click="toggleDrawer()">会话列表</button>
        <div>
          <p class="section-eyebrow">知识问答</p>
          <h1 class="section-title">围绕皮肤问题进行连续问答，获得日常护理与就医参考。</h1>
        </div>
      </div>
    </article>

    <div class="qa-layout">
      <button v-if="drawerOpen" type="button" class="qa-drawer-backdrop" @click="toggleDrawer(false)" />

      <aside class="surface-card qa-sidebar" :class="{ 'is-open': drawerOpen }">
        <div class="qa-sidebar__actions">
          <button type="button" class="primary-button" @click="createNewConversation">新建对话</button>
          <button type="button" class="secondary-button" @click="toggleManageMode">
            {{ manageMode ? '取消管理' : '批量管理' }}
          </button>
        </div>

        <div v-if="manageMode" class="qa-batch-bar">
          <button type="button" class="text-button" @click="toggleSelectAll">
            {{ allSessionsSelected ? '取消全选' : '全选' }}
          </button>
          <span>已选 {{ selectedSessionIds.length }} 项</span>
          <button
            type="button"
            class="text-button qa-batch-bar__danger"
            :disabled="!selectedSessionIds.length"
            @click="batchDeleteDialogOpen = true"
          >
            删除所选
          </button>
        </div>

        <div class="qa-session-list">
          <article v-for="session in sessions" :key="session.session_id" class="qa-session-card" :class="{ 'is-active': activeSessionId === session.session_id }">
            <label v-if="manageMode" class="qa-session-card__checkbox">
              <input
                :checked="selectedSessionIds.includes(session.session_id)"
                type="checkbox"
                @change="toggleSelection(session.session_id)"
              />
            </label>

            <button type="button" class="qa-session-card__main" @click="openSession(session.session_id)">
              <strong>{{ sessionTitle(session) }}</strong>
              <span>{{ formatDateTime(session.updated_at) }}</span>
            </button>

            <button
              v-if="!manageMode"
              type="button"
              class="text-button qa-session-card__delete"
              @click="requestDeleteSession(session.session_id)"
            >
              删除
            </button>
          </article>
        </div>
      </aside>

      <section class="surface-card qa-content">
        <div class="qa-content__head">
          <div>
            <p class="section-eyebrow">知识问答</p>
            <h2 class="card-title">{{ activeSessionTitle }}</h2>
          </div>
          <button type="button" class="secondary-button qa-menu-button qa-menu-button--desktop" @click="toggleDrawer()">会话列表</button>
        </div>

        <div class="qa-recommend">
          <div class="qa-recommend__head">
            <strong>推荐问题</strong>
            <button type="button" class="text-button" @click="createNewConversation">新建对话</button>
          </div>
          <div class="qa-recommend__list">
            <button v-for="prompt in quickQuestions" :key="prompt" type="button" class="qa-recommend__item" @click="askPromptAndSend(prompt)">
              {{ prompt }}
            </button>
          </div>
        </div>

        <PageState
          v-if="loading"
          title="正在加载会话内容"
          description="请稍候，我们正在同步当前对话。"
        />

        <PageState
          v-else-if="loadError && isEmpty"
          tone="error"
          title="会话加载失败"
          :description="loadError"
          action-text="重新加载"
          @action="initialize"
        />

        <PageState
          v-else-if="isEmpty"
          tone="empty"
          title="从一个具体问题开始吧"
          description="您可以点击推荐问题，或直接在底部输入框中提问。"
        />

        <div v-else ref="chatScrollRef" class="qa-thread">
          <article
            v-for="message in messages"
            :key="message.message_id"
            class="qa-message"
            :class="{ 'qa-message--user': message.role === 'user' }"
          >
            <div class="qa-message__meta">
              <span>{{ message.role === 'user' ? '用户' : '智能助手' }}</span>
              <span>{{ formatDateTime(message.created_at) }}</span>
            </div>

            <div class="qa-message__bubble" :class="{ 'is-user': message.role === 'user' }">
              <div v-if="message.role === 'user'" class="qa-message__text">{{ messageText(message.content) }}</div>
              <div v-else class="qa-message__markdown" v-html="renderMarkdown(message.content)" />

              <div v-if="message.role === 'assistant' && message.sources?.length" class="qa-sources">
                <a
                  v-for="(source, index) in message.sources"
                  :key="`${source.url}-${index}`"
                  class="qa-source-link"
                  :href="normalizeUrl(source.url) || undefined"
                  :target="normalizeUrl(source.url) ? '_blank' : undefined"
                  :rel="normalizeUrl(source.url) ? 'noopener noreferrer' : undefined"
                >
                  {{ sourceTitle(source, index) }}
                </a>
              </div>
            </div>
          </article>

          <article v-if="sending" class="qa-message">
            <div class="qa-message__meta">
              <span>智能助手</span>
              <span>正在生成</span>
            </div>
            <div class="qa-message__bubble">
              <p class="qa-typing">{{ statusText }}</p>
            </div>
          </article>
        </div>

        <div class="qa-composer">
          <textarea
            v-model="composer.message"
            class="ghost-textarea qa-composer__input"
            maxlength="2000"
            placeholder="请输入你的问题"
            @keydown="handleComposerKeydown"
          />
          <div class="qa-composer__footer">
            <p>内容由智能助手生成，仅供参考，不能替代专业医疗建议。</p>
            <button type="button" class="primary-button" :disabled="sending" @click="sendMessage">
              {{ sending ? '发送中...' : '发送' }}
            </button>
          </div>
        </div>
      </section>
    </div>

    <ConfirmDialog
      :visible="deleteTargetId !== null"
      title="确认删除该会话？"
      description="删除后无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      :loading="deleteLoading"
      @cancel="deleteTargetId = null"
      @confirm="deleteTargetId !== null ? handleDelete([deleteTargetId]) : undefined"
    />

    <ConfirmDialog
      :visible="batchDeleteDialogOpen"
      title="确认删除选中的会话？"
      description="删除后无法恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      :loading="deleteLoading"
      @cancel="batchDeleteDialogOpen = false"
      @confirm="handleDelete(selectedSessionIds)"
    />
  </section>
</template>

<style scoped>
.qa-banner__row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.qa-layout {
  position: relative;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 18px;
}

.qa-sidebar,
.qa-content {
  min-height: 720px;
}

.qa-sidebar {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 16px;
}

.qa-sidebar__actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.qa-batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: rgba(248, 250, 255, 0.98);
  color: var(--text-sub);
  font-size: 13px;
}

.qa-batch-bar__danger {
  color: var(--rose);
}

.qa-session-list {
  display: grid;
  align-content: start;
  gap: 10px;
  min-height: 0;
  overflow: auto;
}

.qa-session-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(248, 250, 255, 0.98);
}

.qa-session-card.is-active {
  border-color: rgba(47, 125, 255, 0.46);
  box-shadow: var(--shadow-sm);
}

.qa-session-card__main {
  min-height: auto;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
}

.qa-session-card__main strong,
.qa-session-card__main span {
  display: block;
}

.qa-session-card__main strong {
  color: var(--text-strong);
  font-size: 14px;
  line-height: 1.7;
}

.qa-session-card__main span {
  margin-top: 6px;
  color: var(--text-faint);
  font-size: 12px;
}

.qa-content {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  gap: 16px;
}

.qa-content__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.qa-menu-button {
  display: none;
}

.qa-menu-button--desktop {
  display: inline-flex;
}

.qa-recommend {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(248, 250, 255, 0.98);
}

.qa-recommend__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.qa-recommend__head strong {
  color: var(--text-strong);
  font-size: 16px;
}

.qa-recommend__list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.qa-recommend__item {
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.98);
  color: var(--blue);
  font-weight: 700;
}

.qa-thread {
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-right: 6px;
}

.qa-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.qa-message--user {
  align-items: flex-end;
}

.qa-message__meta {
  display: flex;
  gap: 10px;
  color: var(--text-faint);
  font-size: 12px;
}

.qa-message__bubble {
  width: min(100%, 820px);
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(248, 250, 255, 0.98);
  box-shadow: var(--shadow-sm);
}

.qa-message__bubble.is-user {
  width: min(100%, 520px);
  color: #ffffff;
  border: 0;
  background: var(--gradient-main);
}

.qa-message__text,
.qa-typing {
  margin: 0;
  font-size: 14px;
  line-height: 1.9;
  white-space: pre-wrap;
}

.qa-message__markdown {
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.9;
}

.qa-message__markdown :deep(*) {
  box-sizing: border-box;
}

.qa-message__markdown :deep(> :first-child) {
  margin-top: 0;
}

.qa-message__markdown :deep(> :last-child) {
  margin-bottom: 0;
}

.qa-message__markdown :deep(p),
.qa-message__markdown :deep(li) {
  color: var(--text-main);
}

.qa-message__markdown :deep(a) {
  color: var(--blue);
}

.qa-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.qa-source-link {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(47, 125, 255, 0.08);
  color: var(--blue);
  font-size: 12px;
  font-weight: 700;
}

.qa-composer {
  padding-top: 14px;
  border-top: 1px solid rgba(168, 188, 224, 0.4);
}

.qa-composer__input {
  min-height: 100px;
}

.qa-composer__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 12px;
}

.qa-composer__footer p {
  margin: 0;
  color: var(--text-faint);
  font-size: 12px;
}

.qa-drawer-backdrop {
  display: none;
}

@media (max-width: 980px) {
  .qa-layout {
    grid-template-columns: 1fr;
  }

  .qa-menu-button {
    display: inline-flex;
  }

  .qa-menu-button--desktop {
    display: none;
  }

  .qa-sidebar {
    position: fixed;
    top: 12px;
    left: 12px;
    bottom: 12px;
    z-index: 40;
    width: min(320px, calc(100% - 24px));
    transform: translateX(-120%);
    transition: transform 0.22s ease;
  }

  .qa-sidebar.is-open {
    transform: translateX(0);
  }

  .qa-drawer-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 35;
    border: 0;
    background: rgba(17, 31, 55, 0.28);
  }

  .qa-content {
    min-height: 640px;
  }

  .qa-content__head,
  .qa-composer__footer,
  .qa-banner__row {
    align-items: stretch;
    flex-direction: column;
  }

  .qa-message__bubble,
  .qa-message__bubble.is-user {
    width: 100%;
  }
}
</style>
