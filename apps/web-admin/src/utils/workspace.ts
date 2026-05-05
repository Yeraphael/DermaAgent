export function splitVisibleText(value?: string | null) {
  if (!value) return []
  const items = value
    .split(/\r?\n|[；;]+/)
    .map((item) => item.trim().replace(/^[\d.\-、\s]+/, ''))
    .filter(Boolean)
  return items.length ? items : [value.trim()]
}

export function statusLabel(status?: string | null) {
  const map: Record<string, string> = {
    PENDING_AI: '待分析',
    AI_DONE: 'AI 已完成',
    WAIT_DOCTOR: '待医生处理',
    DOCTOR_REPLIED: '医生已回复',
    CLOSED: '已关闭',
  }
  return status ? map[status] || status : '处理中'
}

export function riskLabel(risk?: string | null) {
  const map: Record<string, string> = {
    LOW: '低风险',
    MEDIUM: '中风险',
    HIGH: '高风险',
  }
  return risk ? map[risk] || risk : '待评估'
}

export function statusTone(status?: string | null) {
  if (status === 'WAIT_DOCTOR') return 'amber'
  if (status === 'DOCTOR_REPLIED') return 'mint'
  if (status === 'AI_DONE') return 'blue'
  if (status === 'CLOSED') return 'slate'
  return 'violet'
}

export function riskTone(risk?: string | null) {
  if (risk === 'HIGH') return 'rose'
  if (risk === 'MEDIUM') return 'amber'
  if (risk === 'LOW') return 'mint'
  return 'slate'
}

export function formatPercent(value?: number | null, digits = 0) {
  if (value === undefined || value === null || Number.isNaN(value)) return '--'
  return `${Number(value).toFixed(digits)}%`
}

export function formatDateTime(value?: string | null) {
  return value || '--'
}

export function safeName(value?: string | null, fallback = '未命名') {
  return value?.trim() || fallback
}

export function auditStatusLabel(status?: string | null) {
  const map: Record<string, string> = {
    PENDING: '待审核',
    APPROVED: '已通过',
    REJECTED: '已驳回',
  }
  return status ? map[status] || status : '待审核'
}

export function auditStatusTone(status?: string | null) {
  if (status === 'APPROVED') return 'mint'
  if (status === 'REJECTED') return 'rose'
  return 'amber'
}

export function serviceStatusLabel(status?: number | null) {
  return status === 1 ? '服务中' : '已暂停'
}

export function serviceStatusTone(status?: number | null) {
  return status === 1 ? 'mint' : 'slate'
}

export function accuracyLabel(value?: string | null) {
  const map: Record<string, string> = {
    ACCURATE: '准确',
    PARTIAL: '部分准确',
    INACCURATE: '不准确',
  }
  return value ? map[value] || value : '未反馈'
}

export function accuracyTone(value?: string | null) {
  if (value === 'ACCURATE') return 'mint'
  if (value === 'PARTIAL') return 'amber'
  if (value === 'INACCURATE') return 'rose'
  return 'slate'
}

export function yesNoLabel(value?: number | boolean | null, yes = '是', no = '否') {
  return value ? yes : no
}

export function healthScoreTone(score?: number | null) {
  if (!score && score !== 0) return 'slate'
  if (score >= 80) return 'mint'
  if (score >= 60) return 'blue'
  return 'amber'
}

export function cleanVisibleText(value?: string | null, fallback = '--') {
  if (!value || !value.trim()) return fallback
  return value
    .replace(/LangGraph/gi, '智能流程')
    .replace(/Tavily/gi, '联网检索')
    .replace(/Fallback/gi, '备用处理')
    .replace(/\bmock\b/gi, '标准')
    .replace(/\bdemo\b/gi, '')
    .replace(/\btest\b/gi, '')
    .replace(/local debug/gi, '')
    .replace(/\s{2,}/g, ' ')
    .trim() || fallback
}

export function compactList(items: Array<string | null | undefined>, size = 4) {
  return items.map((item) => cleanVisibleText(item, '')).filter(Boolean).slice(0, size)
}

export function buildAvatarData(name?: string | null, accent: 'blue' | 'mint' = 'blue') {
  const safe = safeName(name, '用户').slice(0, 2)
  const end = accent === 'mint' ? '#bfeeed' : '#bfd2ff'
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#dbe8ff"/>
          <stop offset="100%" stop-color="${end}"/>
        </linearGradient>
      </defs>
      <rect width="120" height="120" rx="34" fill="url(#g)"/>
      <circle cx="60" cy="42" r="20" fill="rgba(255,255,255,.88)"/>
      <path d="M24 100c6-18 20-28 36-28s30 10 36 28" fill="rgba(255,255,255,.88)"/>
      <text x="60" y="108" text-anchor="middle" font-size="15" fill="#345d95" font-family="sans-serif">${safe}</text>
    </svg>
  `
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

export function resolveAvatar(url?: string | null, name?: string | null, accent: 'blue' | 'mint' = 'blue') {
  return url || buildAvatarData(name, accent)
}

export function parseConfigValue(value: string, type = 'text') {
  if (type === 'boolean') {
    return value.trim().toLowerCase() === 'true'
  }
  if (type === 'number') {
    return Number(value)
  }
  if (type === 'json') {
    try {
      return JSON.parse(value)
    } catch {
      return value
    }
  }
  return value
}

export function stringifyConfigValue(value: unknown) {
  if (typeof value === 'string') return value
  return JSON.stringify(value, null, 2)
}
