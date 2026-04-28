export type PortalRisk = 'LOW' | 'MEDIUM' | 'HIGH'
export type PortalStatus = 'WAIT_ANALYSIS' | 'AI_DONE' | 'WAIT_DOCTOR' | 'DOCTOR_REPLIED'

export type PortalDirection = {
  label: string
  value: number
}

export type PortalConsultation = {
  caseId: number
  caseNo: string
  title: string
  submittedAt: string
  onsetDuration: string
  itchLevel: number
  painLevel: number
  spreadFlag: boolean
  spreadParts: string[]
  visuals: string[]
  description: string
  status: PortalStatus
  riskLevel: PortalRisk
  ai: {
    observation: string
    directions: PortalDirection[]
    careAdvice: string[]
    recommendation: string
    shouldVisit: boolean
    riskReason: string
    disclaimer: string
  }
  doctorReply?: {
    doctorName: string
    title: string
    content: string
    suggestion: string[]
    repliedAt: string
  }
}

export type PortalQuestionHistory = {
  id: number
  question: string
  answer: string
  reference: string
  createdAt: string
}

export type PortalNotification = {
  id: number
  category: 'AI' | 'DOCTOR' | 'SYSTEM'
  title: string
  summary: string
  time: string
  linkedCaseId?: number
}

export type PortalSession = {
  access_token: string
  profile: {
    username: string
    real_name: string
    city: string
    age: number
    skin_type: string
    level: string
  }
}

type PortalState = {
  consultations: PortalConsultation[]
  qaHistory: PortalQuestionHistory[]
  notifications: PortalNotification[]
}

type SubmitConsultationPayload = {
  description: string
  onsetDuration: string
  itchLevel: number
  painLevel: number
  spreadFlag: boolean
  spreadParts: string[]
  visuals: string[]
}

type StorageBag = {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

const STATE_KEY = 'derma-mobile-portal-state'
const SESSION_KEY = 'derma-mobile-session'

const profile = {
  username: 'user01',
  real_name: '林知夏',
  city: '上海',
  age: 27,
  skin_type: '混合偏敏',
  level: '年度护理计划',
}

function createVisual(base: string, accent: string, highlight: string) {
  return `linear-gradient(135deg, ${base} 0%, ${accent} 48%, ${highlight} 100%)`
}

const seededVisuals = [
  createVisual('#f6d6cb', '#f0b9b3', '#ffd2d9'),
  createVisual('#f7d8cb', '#eeb3b1', '#f9c8d5'),
  createVisual('#f5d7cb', '#efb7bf', '#ffd8c6'),
]

const initialState: PortalState = {
  consultations: [
    {
      caseId: 201001,
      caseNo: 'AI-20260421-001',
      title: '面颊泛红伴轻度瘙痒',
      submittedAt: '04-21 10:24',
      onsetDuration: '2 天内',
      itchLevel: 3,
      painLevel: 1,
      spreadFlag: false,
      spreadParts: ['面部'],
      visuals: seededVisuals,
      description: '两颊突然出现发红与轻微瘙痒，最近更换了洁面产品，热风环境下会明显加重。',
      status: 'DOCTOR_REPLIED',
      riskLevel: 'MEDIUM',
      ai: {
        observation: '可见面颊与下巴区域片状潮红，局部伴轻度丘疹，整体更像刺激后屏障受损并伴有轻度炎症。',
        directions: [
          { label: '接触性皮炎', value: 45 },
          { label: '湿疹样反应', value: 25 },
          { label: '玫瑰痤疮', value: 15 },
          { label: '屏障受损', value: 15 },
        ],
        careAdvice: [
          '暂停新增护肤品，优先使用温和洁面与修护保湿产品。',
          '避免热水、酒精喷雾和过度清洁，减少刺激叠加。',
          '如果 48 小时内继续扩散或出现灼热加重，建议线下面诊。',
        ],
        recommendation: '当前更建议以修护观察为主，并结合医生回复做进一步判断。',
        shouldVisit: false,
        riskReason: '当前属于中低风险，主要问题是刺激性泛红与屏障受损。',
        disclaimer: '仅供辅助参考，不作为最终诊断依据。',
      },
      doctorReply: {
        doctorName: '张医生',
        title: '皮肤科 主治医师',
        content: '结合图片和描述，考虑更偏向刺激性皮炎或护肤品不耐受。建议先精简护肤，重点保湿修护，避免热刺激和揉搓。',
        suggestion: [
          '温和清洁，每日 2 次以内。',
          '减少刺激性活性成分叠加。',
          '如果持续加重或出现渗液，请尽快线下面诊。',
        ],
        repliedAt: '04-21 14:36',
      },
    },
    {
      caseId: 201002,
      caseNo: 'AI-20260420-009',
      title: '下巴密集丘疹与出油增加',
      submittedAt: '04-20 19:18',
      onsetDuration: '3 天内',
      itchLevel: 1,
      painLevel: 2,
      spreadFlag: false,
      spreadParts: ['下巴'],
      visuals: [
        createVisual('#f5d2c5', '#efb8b5', '#ffcad7'),
        createVisual('#f8dfd1', '#f1c2c0', '#ffd2d2'),
      ],
      description: '口周和下巴爆出较多小丘疹，最近作息不规律，偶有轻微疼痛。',
      status: 'AI_DONE',
      riskLevel: 'LOW',
      ai: {
        observation: '下巴与口周可见密集炎性丘疹，尚未见明显囊肿或结节，整体更接近轻中度炎症性痤疮。',
        directions: [
          { label: '轻中度痤疮', value: 58 },
          { label: '口周皮炎', value: 22 },
          { label: '屏障受损', value: 12 },
          { label: '激素依赖', value: 8 },
        ],
        careAdvice: [
          '晚间清洁后使用清爽保湿产品。',
          '不要频繁挤压和叠加多种祛痘成分。',
          '保持规律作息，观察 1 周变化。',
        ],
        recommendation: '先从护理与生活习惯调整入手，如持续反复可申请医生复核。',
        shouldVisit: false,
        riskReason: '当前炎症程度较轻，没有明显高风险提示。',
        disclaimer: '仅供辅助参考，不作为最终诊断依据。',
      },
    },
    {
      caseId: 201003,
      caseNo: 'AI-20260418-004',
      title: '面部干燥脱皮并伴灼热感',
      submittedAt: '04-18 08:55',
      onsetDuration: '5 天',
      itchLevel: 2,
      painLevel: 3,
      spreadFlag: true,
      spreadParts: ['面部', '鼻翼'],
      visuals: [
        createVisual('#f2d4c4', '#eab8a8', '#f9d0c7'),
      ],
      description: '最近频繁去角质后出现干燥脱皮，洗脸后灼热和刺痛，范围正在扩大到鼻翼。',
      status: 'WAIT_DOCTOR',
      riskLevel: 'MEDIUM',
      ai: {
        observation: '可见较明显的面部干燥脱屑与片状潮红，提示屏障受损并伴刺激性反应。',
        directions: [
          { label: '屏障受损', value: 51 },
          { label: '刺激性皮炎', value: 28 },
          { label: '脂溢性皮炎', value: 11 },
          { label: '湿疹', value: 10 },
        ],
        careAdvice: [
          '立即停止去角质和酸类产品，优先进行修护。',
          '避免热水和磨砂，清洁次数控制在早晚各一次。',
          '若刺痛持续加重，建议尽快面诊。',
        ],
        recommendation: '已建议医生复核，等待进一步回复。',
        shouldVisit: true,
        riskReason: '虽然未见明显急症信号，但灼热和扩散提示需要谨慎观察。',
        disclaimer: '仅供辅助参考，不作为最终诊断依据。',
      },
    },
  ],
  qaHistory: [
    {
      id: 1,
      question: '湿疹和过敏有什么区别？',
      answer: '湿疹更强调皮肤屏障受损后的炎症反应，常伴反复瘙痒和干燥。过敏更强调对外界刺激或成分的免疫反应，通常需要结合接触史来判断。',
      reference: '特应性皮炎与接触性皮炎护理指引',
      createdAt: '04-21 11:42',
    },
    {
      id: 2,
      question: '面部泛红时还能刷酸吗？',
      answer: '不建议在屏障受损和泛红明显时继续刷酸，应先修护并观察，等皮肤状态稳定后再评估是否恢复使用。',
      reference: '敏感肌护理共识',
      createdAt: '04-20 18:32',
    },
  ],
  notifications: [
    {
      id: 1,
      category: 'AI',
      title: '智能分析已完成',
      summary: '你提交的图文问诊已生成初步观察与护理建议。',
      time: '14:30',
      linkedCaseId: 201002,
    },
    {
      id: 2,
      category: 'DOCTOR',
      title: '医生已回复',
      summary: '张医生已补充面部泛红案例的专业建议。',
      time: '14:36',
      linkedCaseId: 201001,
    },
    {
      id: 3,
      category: 'SYSTEM',
      title: '护理指南已更新',
      summary: '新增夏季敏感肌护理指南，可前往知识问答查看。',
      time: '09:10',
    },
  ],
}

function getStorage(): StorageBag {
  const scope = globalThis as {
    localStorage?: Storage
    uni?: {
      getStorageSync(key: string): unknown
      setStorageSync(key: string, value: string): void
      removeStorageSync(key: string): void
    }
  }

  if (scope.localStorage) {
    return {
      getItem: (key) => scope.localStorage?.getItem(key) ?? null,
      setItem: (key, value) => scope.localStorage?.setItem(key, value),
      removeItem: (key) => scope.localStorage?.removeItem(key),
    }
  }

  return {
    getItem: (key) => {
      const value = scope.uni?.getStorageSync(key)
      return typeof value === 'string' ? value : value ? JSON.stringify(value) : null
    },
    setItem: (key, value) => scope.uni?.setStorageSync(key, value),
    removeItem: (key) => scope.uni?.removeStorageSync(key),
  }
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function readState(): PortalState {
  const storage = getStorage()
  const raw = storage.getItem(STATE_KEY)
  if (!raw) {
    const seeded = clone(initialState)
    storage.setItem(STATE_KEY, JSON.stringify(seeded))
    return seeded
  }

  try {
    return JSON.parse(raw) as PortalState
  } catch {
    const seeded = clone(initialState)
    storage.setItem(STATE_KEY, JSON.stringify(seeded))
    return seeded
  }
}

function writeState(state: PortalState) {
  getStorage().setItem(STATE_KEY, JSON.stringify(state))
}

function mutateState<T>(handler: (state: PortalState) => T): T {
  const state = readState()
  const result = handler(state)
  writeState(state)
  return result
}

function getStatusLabel(status: PortalStatus) {
  return {
    WAIT_ANALYSIS: '等待分析',
    AI_DONE: '智能已完成',
    WAIT_DOCTOR: '等待医生',
    DOCTOR_REPLIED: '医生已回复',
  }[status]
}

function buildDirections(description: string, itchLevel: number, painLevel: number, spreadFlag: boolean): PortalDirection[] {
  const lower = description.toLowerCase()
  if (lower.includes('痘') || lower.includes('丘疹') || lower.includes('acne') || lower.includes('pimple')) {
    return [
      { label: '轻中度痤疮', value: 55 },
      { label: '口周皮炎', value: 20 },
      { label: '屏障受损', value: 15 },
      { label: '激素依赖', value: 10 },
    ]
  }

  if (lower.includes('脱皮') || lower.includes('干') || lower.includes('dry')) {
    return [
      { label: '屏障受损', value: 48 },
      { label: '刺激性皮炎', value: 28 },
      { label: '湿疹', value: 14 },
      { label: '脂溢性皮炎', value: 10 },
    ]
  }

  if (spreadFlag || itchLevel >= 4 || painLevel >= 4) {
    return [
      { label: '湿疹样反应', value: 34 },
      { label: '接触性皮炎', value: 28 },
      { label: '炎症扩散', value: 22 },
      { label: '感染风险', value: 16 },
    ]
  }

  return [
    { label: '接触性皮炎', value: 42 },
    { label: '湿疹样反应', value: 26 },
    { label: '玫瑰痤疮', value: 17 },
    { label: '屏障受损', value: 15 },
  ]
}

function synthesizeConsultationTitle(description: string) {
  if (!description.trim()) return '图文问诊'
  return description.replace(/[，。！？；,.!?]/g, ' ').trim().slice(0, 14)
}

function synthesizeRisk(itchLevel: number, painLevel: number, spreadFlag: boolean, description: string): PortalRisk {
  const lower = description.toLowerCase()
  if (spreadFlag || painLevel >= 4 || lower.includes('渗液') || lower.includes('发热')) return 'HIGH'
  if (itchLevel >= 3 || painLevel >= 3 || lower.includes('灼热') || lower.includes('扩散')) return 'MEDIUM'
  return 'LOW'
}

function synthesizeObservation(description: string, risk: PortalRisk) {
  if (risk === 'HIGH') {
    return `根据你提交的描述，当前皮损可能存在较明显的炎症扩散信号。${description.slice(0, 48)}，建议尽快结合医生判断。`
  }
  if (risk === 'MEDIUM') {
    return `系统初步观察到你描述的问题更偏向刺激或炎症反应。${description.slice(0, 44)}，建议先做好护理并留意变化。`
  }
  return `当前描述更偏向轻度、局部的皮肤问题。${description.slice(0, 40)}，可先参考护理建议并观察。`
}

function buildCareAdvice(risk: PortalRisk, description: string) {
  const lower = description.toLowerCase()
  const list = [
    '保持温和清洁，避免频繁摩擦和热水刺激。',
    '优先使用简单修护保湿产品，暂停最近新增的高活性护肤品。',
  ]

  if (lower.includes('痘') || lower.includes('丘疹') || lower.includes('acne') || lower.includes('pimple')) {
    list.push('不要频繁挤压皮损，夜间可使用轻薄型保湿产品并注意作息。')
  } else {
    list.push('减少酒精、香精和去角质类产品叠加使用。')
  }

  if (risk !== 'LOW') {
    list.push('如果 48 小时内继续加重、扩散或出现明显疼痛，请及时就医。')
  }

  return list
}

function ensureSession() {
  const storage = getStorage()
  const raw = storage.getItem(SESSION_KEY)
  return raw ? (JSON.parse(raw) as PortalSession) : null
}

export function getPortalSession() {
  return ensureSession()
}

export function setPortalSession(session: PortalSession) {
  getStorage().setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearPortalSession() {
  getStorage().removeItem(SESSION_KEY)
}

export async function loginPortalUser(username: string, password: string) {
  if (username !== 'user01' || password !== '12345678') {
    throw new Error('请使用演示账号 user01 / 12345678 登录。')
  }

  const session: PortalSession = {
    access_token: `mock-user-${Date.now()}`,
    profile,
  }
  setPortalSession(session)
  return session
}

export function getPortalStatusLabel(status: PortalStatus) {
  return getStatusLabel(status)
}

export function getPortalRiskLabel(risk: PortalRisk) {
  return {
    LOW: '低风险',
    MEDIUM: '中风险',
    HIGH: '高风险',
  }[risk]
}

export function buildVisualStyle(value: string) {
  const trimmed = value.trim()
  if (trimmed.startsWith('url(') || trimmed.startsWith('http') || trimmed.startsWith('blob:') || trimmed.startsWith('data:image/')) {
    return {
      backgroundImage: trimmed.startsWith('url(') ? trimmed : `url(${trimmed})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  return {
    background: value,
  }
}

export function getPortalDashboard() {
  const state = readState()
  const unread = state.notifications.length
  const doctorReplies = state.consultations.filter((item) => item.status === 'DOCTOR_REPLIED').length
  const waiting = state.consultations.filter((item) => item.status === 'WAIT_DOCTOR').length

  return {
    profile,
    summary: {
      consultationTotal: state.consultations.length,
      waitingTotal: waiting,
      doctorReplyTotal: doctorReplies,
      unreadNotifications: unread,
    },
    featuredGuide: {
      title: '夏季皮肤防护指南',
      subtitle: '科学护理 · 远离敏感',
      copy: '建立轻量护肤和防晒节奏，帮助敏感肌减少波动。',
    },
    ongoingCase: state.consultations[0],
    recentCases: state.consultations.slice(0, 3),
    notifications: state.notifications,
    quickActions: [
      { key: 'consultation', label: '图文问诊', description: '上传图片与症状' },
      { key: 'analysis', label: '智能分析', description: '查看结果报告' },
      { key: 'qa', label: '知识问答', description: '护理与科普' },
      { key: 'history', label: '历史记录', description: '问诊与通知' },
    ],
  }
}

export function getPortalConsultations() {
  return readState().consultations
}

export function getPortalConsultation(caseId: number) {
  return readState().consultations.find((item) => item.caseId === caseId) || null
}

export function getPortalNotifications() {
  return readState().notifications
}

export function getPortalProfile() {
  const state = readState()
  const lastDoctorReply = state.consultations.find((item) => item.doctorReply)
  return {
    profile,
    carePlan: [
      '避免高频去角质，维持稳定的温和清洁与修护保湿。',
      '敏感或泛红期间，优先降低护肤复杂度并做好防晒。',
      '保持睡眠节律与饮食规律，减少爆痘与敏感反复。',
    ],
    healthArchive: {
      skinType: profile.skin_type,
      allergies: ['酒精香精', '高浓度酸类'],
      habits: ['换季时容易叠加护肤品', '工作日熬夜较多'],
      latestDoctor: lastDoctorReply?.doctorReply?.doctorName || '张医生',
      riskTrend: ['最近 30 天中风险 2 次', '低风险 1 次', '高风险 0 次'],
    },
  }
}

export function getPortalQaSnapshot() {
  const state = readState()
  return {
    suggestions: [
      '湿疹和过敏有什么区别？',
      '如何判断是不是屏障受损？',
      '敏感肌如何选择护肤品？',
      '泛红期间可以自行恢复吗？',
    ],
    history: state.qaHistory,
  }
}

export async function askPortalQuestion(question: string) {
  const lowered = question.toLowerCase()
  let answer = '建议先减少刺激源，观察是否与近期护肤、作息或环境变化有关。如果持续加重，最好结合图文问诊进一步判断。'
  let reference = '通用皮肤护理建议'

  if (lowered.includes('湿疹') || lowered.includes('过敏')) {
    answer = '湿疹更像是皮肤屏障受损后的炎症反复，通常会伴随瘙痒和干燥。过敏则更强调对外界成分或刺激的反应，需要结合接触史来判断。'
    reference = '特应性皮炎与接触性皮炎护理指引'
  } else if (lowered.includes('泛红') || lowered.includes('屏障')) {
    answer = '如果在清洁、热刺激或活性护肤后更容易出现泛红、刺痛和紧绷，往往提示屏障受损。此时不建议继续刷酸，应该先修护。'
    reference = '敏感肌与屏障修护共识'
  } else if (lowered.includes('痘')) {
    answer = '痘痘反复往往和作息、压力、清洁方式以及护肤品叠加有关。建议把重点放在温和清洁、轻量保湿和规律睡眠上。'
    reference = '轻中度痤疮护理建议'
  }

  const record: PortalQuestionHistory = {
    id: Date.now(),
    question,
    answer,
    reference,
    createdAt: '04-21 15:12',
  }

  mutateState((state) => {
    state.qaHistory.unshift(record)
    if (state.qaHistory.length > 8) {
      state.qaHistory = state.qaHistory.slice(0, 8)
    }
  })

  return record
}

export async function submitPortalConsultation(payload: SubmitConsultationPayload) {
  const risk = synthesizeRisk(payload.itchLevel, payload.painLevel, payload.spreadFlag, payload.description)
  const directions = buildDirections(payload.description, payload.itchLevel, payload.painLevel, payload.spreadFlag)
  const nextCaseId = Number(`20${Date.now().toString().slice(-5)}`)
  const title = synthesizeConsultationTitle(payload.description)

  const caseRecord: PortalConsultation = {
    caseId: nextCaseId,
    caseNo: `AI-${new Date().getFullYear()}${String(Date.now()).slice(-8)}`,
    title,
    submittedAt: '刚刚',
    onsetDuration: payload.onsetDuration,
    itchLevel: payload.itchLevel,
    painLevel: payload.painLevel,
    spreadFlag: payload.spreadFlag,
    spreadParts: payload.spreadParts,
    visuals: payload.visuals.length ? payload.visuals : seededVisuals,
    description: payload.description,
    status: risk === 'LOW' ? 'AI_DONE' : 'WAIT_DOCTOR',
    riskLevel: risk,
    ai: {
      observation: synthesizeObservation(payload.description, risk),
      directions,
      careAdvice: buildCareAdvice(risk, payload.description),
      recommendation: risk === 'HIGH'
        ? '当前建议尽快就医，并等待医生尽快回复。'
        : risk === 'MEDIUM'
          ? '先按护理建议处理，并留意是否扩散或加重。'
          : '当前更适合先居家护理与观察。',
      shouldVisit: risk !== 'LOW',
      riskReason: risk === 'HIGH'
        ? '存在扩散、疼痛或高炎症信号，需要医生和线下就医共同评估。'
        : risk === 'MEDIUM'
          ? '属于需要重点观察和医生复核的中风险情况。'
          : '当前偏轻度，暂未见明显危险信号。',
      disclaimer: '仅供辅助参考，不作为最终诊断依据。',
    },
  }

  mutateState((state) => {
    state.consultations.unshift(caseRecord)
    state.notifications.unshift({
      id: Date.now(),
      category: 'AI',
      title: '新的智能分析已生成',
      summary: `${title} 已生成初步观察与护理建议。`,
      time: '刚刚',
      linkedCaseId: caseRecord.caseId,
    })
  })

  return caseRecord
}
