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
  [/测试编号/g, ''],
  [/\be\d{4,}\b/gi, ''],
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

  let text = String(value).replace(/\r/g, '')
  for (const [pattern, replacement] of REMOVAL_RULES) {
    text = text.replace(pattern, replacement)
  }

  const normalized = text
    .split('\n')
    .map((line) => line.replace(/\s+/g, ' ').trim())
    .filter((line, index, lines) => Boolean(line) || (index > 0 && Boolean(lines[index - 1])))
    .join('\n')
    .trim()

  return normalized || fallback
}

export function sanitizeVisibleList(values: Array<string | null | undefined>) {
  return values.map((item) => sanitizeVisibleText(item)).filter(Boolean)
}

export function splitParagraphs(value?: string | null) {
  return sanitizeVisibleText(value)
    .split(/\r?\n|[；;。]/)
    .map((item) => item.trim().replace(/^[\-\u2022\d.\s]+/, ''))
    .filter(Boolean)
}

export function formatDateTime(value?: string | null, fallback = '--') {
  const text = sanitizeVisibleText(value)
  return text || fallback
}

export function formatDate(value?: string | null, fallback = '--') {
  const text = sanitizeVisibleText(value)
  return text ? text.slice(0, 10) : fallback
}

export function maskPhone(value?: string | null) {
  const digits = (value || '').replace(/\D/g, '')
  if (digits.length !== 11) {
    return sanitizeVisibleText(value)
  }
  return `${digits.slice(0, 3)} **** ${digits.slice(-4)}`
}

export function getInitial(value?: string | null) {
  const text = sanitizeVisibleText(value, '肤')
  return text.slice(0, 1).toUpperCase()
}

export function getRiskLabel(value?: string | null) {
  return value ? RISK_LABELS[value] || sanitizeVisibleText(value, '待评估') : '待评估'
}

export function getRiskTone(value?: string | null) {
  if (value === 'HIGH') return 'rose'
  if (value === 'MEDIUM') return 'amber'
  if (value === 'LOW') return 'mint'
  return 'slate'
}

export function getStatusLabel(value?: string | null) {
  return value ? STATUS_LABELS[value] || sanitizeVisibleText(value, '处理中') : '处理中'
}

export function getStatusTone(value?: string | null) {
  if (value === 'DOCTOR_REPLIED') return 'mint'
  if (value === 'WAIT_DOCTOR') return 'amber'
  if (value === 'AI_DONE') return 'blue'
  if (value === 'CLOSED') return 'slate'
  return 'violet'
}

export function levelLabel(index: number) {
  return SYMPTOM_LEVELS[Math.max(0, Math.min(index, SYMPTOM_LEVELS.length - 1))]
}

export function parseConsultationNarrative(value?: string | null) {
  const text = sanitizeVisibleText(value)
  const lines = text.split('\n').map((line) => line.trim()).filter(Boolean)
  const detailMap: Record<string, string> = {}

  for (const line of lines) {
    const match = line.match(/^([^：:]+)[：:]\s*(.+)$/)
    if (match) {
      detailMap[match[1].trim()] = match[2].trim()
    }
  }

  const complaint = detailMap['主诉描述'] || lines[0] || ''
  return {
    complaint,
    onsetDuration: detailMap['发病时长'] || '',
    spread: detailMap['是否扩散'] || '',
    itchLevel: detailMap['瘙痒程度'] || '',
    painLevel: detailMap['疼痛程度'] || '',
    areas: detailMap['发生部位'] || '',
    medication: detailMap['是否使用过药物或护肤品'] || '',
  }
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

export function guessSuggestionDetail(title: string) {
  const text = sanitizeVisibleText(title)
  if (text.includes('清洁')) return '选择温和、低刺激的清洁产品，避免频繁去角质和过度清洗。'
  if (text.includes('保湿')) return '坚持使用修护型保湿产品，帮助稳定皮肤屏障，减少紧绷和刺痛。'
  if (text.includes('刺激')) return '尽量避开酒精、香精、刷酸和高温环境，降低额外刺激。'
  if (text.includes('防晒')) return '外出前做好物理或化学防晒，避免暴晒带来的反复泛红。'
  return '建议持续观察症状变化，结合近期作息、饮食和护肤调整来优化护理方案。'
}
