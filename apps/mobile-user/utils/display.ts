const REMOVAL_RULES: Array<[RegExp, string]> = [
  [/用户端/g, ''],
  [/默认演示账号/g, ''],
  [/演示账号/g, ''],
  [/mock 数据/gi, ''],
  [/后端真实数据/g, ''],
  [/H5 测试/gi, ''],
  [/小程序迁移/g, ''],
  [/LangGraph/gi, ''],
  [/Tavily/gi, ''],
  [/Fallback/gi, ''],
  [/路由分发/g, ''],
  [/工具调用/g, ''],
  [/智能图文辅助分析结果/g, '智能分析结果'],
  [/所有关键节点都收口在同一条时间线/g, ''],
  [/不再使用演示状态/g, ''],
  [/测试数据/g, ''],
  [/开发调试/g, ''],
  [/模型路由/g, ''],
  [/主节点/g, ''],
  [/分支节点/g, ''],
]

const RISK_LABELS: Record<string, string> = {
  LOW: '低风险',
  MEDIUM: '中风险',
  HIGH: '高风险',
}

const STATUS_LABELS: Record<string, string> = {
  PENDING_AI: '待分析',
  AI_DONE: '已完成分析',
  WAIT_DOCTOR: '待医生回复',
  DOCTOR_REPLIED: '已回复',
  CLOSED: '已结束',
}

export const SYMPTOM_LEVELS = ['无', '轻微', '中度', '重度', '剧烈'] as const

export function sanitizeVisibleText(value: unknown, fallback = '') {
  if (value === null || value === undefined) {
    return fallback
  }

  let text = String(value)
  for (const [pattern, replacement] of REMOVAL_RULES) {
    text = text.replace(pattern, replacement)
  }

  return text.trim() || fallback
}

export function formatDate(value?: string | null, fallback = '--') {
  const text = sanitizeVisibleText(value)
  return text ? text.slice(0, 10) : fallback
}

export function formatDateTime(value?: string | null, fallback = '--') {
  return sanitizeVisibleText(value, fallback)
}

export function getRiskLabel(value?: string | null) {
  return value ? RISK_LABELS[value] || sanitizeVisibleText(value, '待评估') : '待评估'
}

export function getStatusLabel(value?: string | null) {
  return value ? STATUS_LABELS[value] || sanitizeVisibleText(value, '处理中') : '处理中'
}

export function levelLabel(index: number) {
  return SYMPTOM_LEVELS[Math.max(0, Math.min(index, SYMPTOM_LEVELS.length - 1))]
}

export function buildConsultationNarrative(payload: {
  description: string
  onsetDuration: string
  spread: string
  itchLevel: string
  painLevel: string
  areas: string[]
  medication: string
}) {
  return [
    `主诉描述：${payload.description.trim()}`,
    `发病时长：${payload.onsetDuration}`,
    `是否扩散：${payload.spread}`,
    `瘙痒程度：${payload.itchLevel}`,
    `疼痛程度：${payload.painLevel}`,
    `发生部位：${payload.areas.join('、') || '未填写'}`,
    `是否使用过药物或护肤品：${payload.medication}`,
  ].join('\n')
}

export function parseConsultationNarrative(value?: string | null) {
  const text = sanitizeVisibleText(value)
  const lines = text.split('\n').filter(Boolean)
  const map: Record<string, string> = {}
  for (const line of lines) {
    const match = line.match(/^([^：:]+)[：:]\s*(.+)$/)
    if (match) {
      map[match[1].trim()] = match[2].trim()
    }
  }
  return {
    complaint: map['主诉描述'] || lines[0] || '',
    onsetDuration: map['发病时长'] || '',
    spread: map['是否扩散'] || '',
    itchLevel: map['瘙痒程度'] || '',
    painLevel: map['疼痛程度'] || '',
    areas: map['发生部位'] || '',
    medication: map['是否使用过药物或护肤品'] || '',
  }
}

export function splitSegments(value?: string | null) {
  return sanitizeVisibleText(value)
    .split(/\r?\n|[；;。]/)
    .map((item) => item.trim().replace(/^[\-\u2022\d.\s]+/, ''))
    .filter(Boolean)
}

export function maskPhone(value?: string | null) {
  const digits = (value || '').replace(/\D/g, '')
  if (digits.length !== 11) return sanitizeVisibleText(value)
  return `${digits.slice(0, 3)} **** ${digits.slice(-4)}`
}

export function getInitial(value?: string | null) {
  return sanitizeVisibleText(value, '肤').slice(0, 1).toUpperCase()
}

export function guessSuggestionDetail(title: string) {
  const text = sanitizeVisibleText(title)
  if (text.includes('清洁')) return '建议选择温和清洁方式，避免过度清洗和去角质。'
  if (text.includes('保湿')) return '建议持续做好保湿修护，帮助稳定皮肤屏障。'
  if (text.includes('刺激')) return '建议减少酒精、香精、刷酸和高温环境带来的刺激。'
  if (text.includes('防晒')) return '建议外出时做好防晒，降低日晒引起的反复泛红。'
  return '建议结合近期作息、饮食和护肤变化继续观察。'
}
