export type WorkspaceRole = 'DOCTOR' | 'ADMIN'
export type ConsultationRisk = 'LOW' | 'MEDIUM' | 'HIGH'
export type ConsultationStatus = 'WAIT_DOCTOR' | 'AI_DONE' | 'DOCTOR_REPLIED' | 'CLOSED'
export type AuditStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export type ControlCenterAccount = {
  account_id: number
  username: string
  role_type: WorkspaceRole
  display_name: string
  title: string
}

export type DoctorRecord = {
  doctor_id: number
  account_id: number
  doctor_name: string
  department: string
  hospital_name: string
  title_name: string
  audit_status: AuditStatus
  service_status: 0 | 1
  focus: string
  response_rate: string
  avatar: string
}

export type PatientRecord = {
  patient_id: number
  account_id: number
  name: string
  gender: string
  age: number
  city: string
  skin_type: string
  tags: string[]
  allergies: string[]
  medications: string[]
  habits: string[]
  recent_case_ids: number[]
  avatar: string
  health_score: number
}

export type ConsultationRecord = {
  case_id: number
  case_no: string
  patient_id: number
  doctor_id: number
  summary_title: string
  symptom_summary: string
  onset_duration: string
  itch_level: number
  pain_level: number
  spread_flag: boolean
  spread_parts: string[]
  status: ConsultationStatus
  risk_level: ConsultationRisk
  submitted_at: string
  images: string[]
  ai_result: {
    image_observation: string
    risk_level: ConsultationRisk
    possible_directions: Array<{ label: string; value: number }>
    condition_guess: string
    confidence: number
    advice: string[]
    alert: string
    recommendation: string
  }
  doctor_reply?: {
    first_impression: string
    care_advice: string
    suggest_offline: boolean
    suggest_revisit: boolean
    note: string
    replied_at: string
  }
  ai_feedback?: {
    accuracy: 'ACCURATE' | 'PARTIAL' | 'INACCURATE'
    note: string
  }
}

export type UserRecord = {
  user_id: number
  account_id: number
  username: string
  phone: string
  city: string
  real_name: string
  status: 0 | 1
  latest_case: string
  risk_preference: string
  tag: string
}

export type ConfigRecord = {
  config_key: string
  title: string
  description: string
  config_value: string | number | boolean
  type: 'switch' | 'text' | 'number'
}

export type OperationLog = {
  log_id: number
  operator: string
  module_name: string
  operation_type: string
  operation_desc: string
  created_at: string
  result: 'SUCCESS' | 'FAILED'
}

export type ModelLog = {
  log_id: number
  biz_type: string
  model_name: string
  duration: string
  token_cost: string
  created_at: string
  status: 'SUCCESS' | 'RETRY' | 'FAILED'
  summary: string
}

export type AnnouncementRecord = {
  announcement_id: number
  title: string
  content: string
  scope: 'ALL' | 'DOCTOR' | 'USER'
  created_at: string
}

type ControlCenterState = {
  users: UserRecord[]
  doctors: DoctorRecord[]
  patients: PatientRecord[]
  consultations: ConsultationRecord[]
  configs: ConfigRecord[]
  operationLogs: OperationLog[]
  modelLogs: ModelLog[]
  announcements: AnnouncementRecord[]
}

type DoctorReplyPayload = {
  first_impression: string
  care_advice: string
  suggest_offline: boolean
  suggest_revisit: boolean
  note: string
}

type FeedbackPayload = {
  accuracy: 'ACCURATE' | 'PARTIAL' | 'INACCURATE'
  note: string
}

type AnnouncementPayload = {
  title: string
  content: string
  scope: 'ALL' | 'DOCTOR' | 'USER'
}

const STORAGE_KEY = 'derma-web-control-center-v2'

const adminAccount: ControlCenterAccount = {
  account_id: 9001,
  username: 'admin01',
  role_type: 'ADMIN',
  display_name: '管理员',
  title: '超级管理员',
}

const doctorAccount: ControlCenterAccount = {
  account_id: 7001,
  username: 'doctor01',
  role_type: 'DOCTOR',
  display_name: '张医生',
  title: '皮肤科 副主任医师',
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function makePortrait(initials: string, base: string, accent: string) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${base}" />
          <stop offset="100%" stop-color="${accent}" />
        </linearGradient>
      </defs>
      <rect width="160" height="160" rx="48" fill="url(#g)" />
      <circle cx="80" cy="58" r="30" fill="rgba(255,255,255,.88)" />
      <path d="M35 136c6-24 25-37 45-37s39 13 45 37" fill="rgba(255,255,255,.88)" />
      <text x="80" y="150" text-anchor="middle" font-family="Arial" font-size="22" fill="rgba(14,48,97,.65)">${initials}</text>
    </svg>
  `
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

function makeSkinShot(base: string, accent: string, spots: string[]) {
  const circles = spots
    .map((color, index) => {
      const x = 30 + ((index * 29) % 120)
      const y = 36 + ((index * 41) % 118)
      const radius = 10 + (index % 3) * 8
      return `<circle cx="${x}" cy="${y}" r="${radius}" fill="${color}" opacity="0.72" />`
    })
    .join('')
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="260" height="180" viewBox="0 0 260 180">
      <defs>
        <linearGradient id="skin" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${base}" />
          <stop offset="100%" stop-color="${accent}" />
        </linearGradient>
      </defs>
      <rect width="260" height="180" rx="32" fill="url(#skin)" />
      <ellipse cx="70" cy="40" rx="62" ry="36" fill="rgba(255,255,255,.18)" />
      <ellipse cx="180" cy="150" rx="74" ry="40" fill="rgba(255,255,255,.12)" />
      ${circles}
    </svg>
  `
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

const patientPortraits = [
  makePortrait('LW', '#dfeaff', '#b6c7ff'),
  makePortrait('WM', '#dceefd', '#bde7ff'),
  makePortrait('CZ', '#ece4ff', '#d5c6ff'),
  makePortrait('ZX', '#dff8ff', '#bef0ed'),
  makePortrait('LY', '#efe9ff', '#c9d7ff'),
]

const doctorPortraits = [
  makePortrait('张', '#d6e4ff', '#bfd6ff'),
  makePortrait('李', '#dff3ff', '#c0dcff'),
  makePortrait('王', '#ede4ff', '#cfbdfc'),
  makePortrait('刘', '#dffaf6', '#b8ece3'),
  makePortrait('陈', '#f0e8ff', '#cfdefe'),
]

const mockStateSeed: ControlCenterState = {
  users: [
    {
      user_id: 1,
      account_id: 501,
      username: 'user_liwx',
      phone: '138****0011',
      city: '上海',
      real_name: '李晚雨',
      status: 1,
      latest_case: '面部泛红伴瘙痒',
      risk_preference: '需要医生复核',
      tag: '敏感肌',
    },
    {
      user_id: 2,
      account_id: 502,
      username: 'user_wangm',
      phone: '139****2234',
      city: '杭州',
      real_name: '王子明',
      status: 1,
      latest_case: '躯干红斑脱屑',
      risk_preference: '高风险优先提醒',
      tag: '油痘肌',
    },
    {
      user_id: 3,
      account_id: 503,
      username: 'user_chenz',
      phone: '137****9981',
      city: '广州',
      real_name: '陈思琪',
      status: 1,
      latest_case: '下巴密集丘疹',
      risk_preference: '夜间通知',
      tag: '痤疮管理',
    },
    {
      user_id: 4,
      account_id: 504,
      username: 'user_zhaot',
      phone: '186****5512',
      city: '成都',
      real_name: '赵天宇',
      status: 0,
      latest_case: '眼周闭口',
      risk_preference: '仅 AI 建议',
      tag: '停用观察',
    },
    {
      user_id: 5,
      account_id: 505,
      username: 'user_liuyi',
      phone: '188****7712',
      city: '武汉',
      real_name: '刘佳怡',
      status: 1,
      latest_case: '面部干燥脱皮',
      risk_preference: '复查提醒',
      tag: '屏障修复',
    },
  ],
  doctors: [
    {
      doctor_id: 301,
      account_id: 7001,
      doctor_name: '张晓雨',
      department: '皮肤科',
      hospital_name: '北京协和医院',
      title_name: '副主任医师',
      audit_status: 'APPROVED',
      service_status: 1,
      focus: '面部炎症、敏感肌',
      response_rate: '92.6%',
      avatar: doctorPortraits[0],
    },
    {
      doctor_id: 302,
      account_id: 7002,
      doctor_name: '李晨',
      department: '皮肤科',
      hospital_name: '上海华山医院',
      title_name: '主任医师',
      audit_status: 'APPROVED',
      service_status: 1,
      focus: '银屑病、湿疹',
      response_rate: '89.4%',
      avatar: doctorPortraits[1],
    },
    {
      doctor_id: 303,
      account_id: 7003,
      doctor_name: '王禹',
      department: '皮肤科',
      hospital_name: '中山大学附属第一医院',
      title_name: '副主任医师',
      audit_status: 'PENDING',
      service_status: 1,
      focus: '儿童皮肤病',
      response_rate: '86.1%',
      avatar: doctorPortraits[2],
    },
    {
      doctor_id: 304,
      account_id: 7004,
      doctor_name: '刘桐',
      department: '皮肤科',
      hospital_name: '四川大学华西医院',
      title_name: '主治医师',
      audit_status: 'APPROVED',
      service_status: 0,
      focus: '痤疮、激素依赖性皮炎',
      response_rate: '84.8%',
      avatar: doctorPortraits[3],
    },
    {
      doctor_id: 305,
      account_id: 7005,
      doctor_name: '陈雨涵',
      department: '皮肤科',
      hospital_name: '复旦大学附属华山医院',
      title_name: '住院医师',
      audit_status: 'REJECTED',
      service_status: 0,
      focus: '皮肤护理宣教',
      response_rate: '81.9%',
      avatar: doctorPortraits[4],
    },
  ],
  patients: [
    {
      patient_id: 201,
      account_id: 501,
      name: '李晚雨',
      gender: '女',
      age: 28,
      city: '上海',
      skin_type: '混合偏敏',
      tags: ['敏感肌', '轻度泛红', '近期换护肤品'],
      allergies: ['酒精香精'],
      medications: ['无长期用药'],
      habits: ['熬夜加班', '爱喝咖啡'],
      recent_case_ids: [1001, 1004],
      avatar: patientPortraits[0],
      health_score: 82,
    },
    {
      patient_id: 202,
      account_id: 502,
      name: '王子明',
      gender: '男',
      age: 34,
      city: '杭州',
      skin_type: '油性',
      tags: ['换季泛红', '局部脱屑'],
      allergies: ['无'],
      medications: ['维生素 B 族'],
      habits: ['运动较多', '出汗后清洁不及时'],
      recent_case_ids: [1002],
      avatar: patientPortraits[1],
      health_score: 75,
    },
    {
      patient_id: 203,
      account_id: 503,
      name: '陈思琪',
      gender: '女',
      age: 22,
      city: '广州',
      skin_type: '油痘肌',
      tags: ['下巴爆痘', '作息不规律'],
      allergies: ['无'],
      medications: ['外用阿达帕林'],
      habits: ['常戴口罩', '奶茶频率高'],
      recent_case_ids: [1003],
      avatar: patientPortraits[2],
      health_score: 68,
    },
    {
      patient_id: 204,
      account_id: 504,
      name: '赵天宇',
      gender: '男',
      age: 19,
      city: '成都',
      skin_type: '混合偏油',
      tags: ['眼周闭口', '轻度刺痛'],
      allergies: ['某些防晒成分'],
      medications: ['无'],
      habits: ['夜间熬夜打游戏'],
      recent_case_ids: [1005],
      avatar: patientPortraits[3],
      health_score: 71,
    },
    {
      patient_id: 205,
      account_id: 505,
      name: '刘佳怡',
      gender: '女',
      age: 31,
      city: '武汉',
      skin_type: '干性',
      tags: ['屏障受损', '换季刺痛'],
      allergies: ['高浓度酸类'],
      medications: ['维生素 E'],
      habits: ['频繁去角质'],
      recent_case_ids: [1006],
      avatar: patientPortraits[4],
      health_score: 79,
    },
  ],
  consultations: [
    {
      case_id: 1001,
      case_no: '2026-0621-000128',
      patient_id: 201,
      doctor_id: 301,
      summary_title: '面部泛红伴瘙痒 2 天',
      symptom_summary: '两颊泛红并有轻微刺痒，遇到热风或喷雾后加重，近期更换了清洁产品。',
      onset_duration: '2 天内',
      itch_level: 3,
      pain_level: 1,
      spread_flag: false,
      spread_parts: ['面部'],
      status: 'WAIT_DOCTOR',
      risk_level: 'MEDIUM',
      submitted_at: '2026-04-21 10:24',
      images: [
        makeSkinShot('#f7d8cc', '#f1b4af', ['#eb8d93', '#e37680', '#d95f71', '#e89ca4']),
        makeSkinShot('#f5d3c8', '#e9b0ae', ['#dd7074', '#d86063', '#e38d8f', '#e4a0a2']),
        makeSkinShot('#f7d7cf', '#f2c2b7', ['#e16e7b', '#de5f66', '#eb8a94', '#efb0b6']),
      ],
      ai_result: {
        image_observation: '可见面颊和下巴区域出现片状红斑，局部有轻度丘疹，暂未见明显渗出。',
        risk_level: 'MEDIUM',
        possible_directions: [
          { label: '接触性皮炎', value: 45 },
          { label: '湿疹样反应', value: 25 },
          { label: '玫瑰痤疮', value: 18 },
          { label: '屏障受损', value: 12 },
        ],
        condition_guess: '刺激后屏障受损 / 轻度接触性皮炎',
        confidence: 82,
        advice: [
          '暂停最近新增的活性护肤品，使用温和洁面与修护乳。',
          '避免热水、频繁摩擦和酒精型喷雾，减少刺激源叠加。',
          '48 小时内观察泛红和瘙痒变化，如加重建议医生复核。',
        ],
        alert: '当前暂未见紧急风险，但属于需要医生进一步判断的中风险案例。',
        recommendation: '建议医生复核并给出是否需要线下就诊的明确意见。',
      },
    },
    {
      case_id: 1002,
      case_no: '2026-0621-000129',
      patient_id: 202,
      doctor_id: 301,
      summary_title: '躯干片状红斑脱屑 1 周',
      symptom_summary: '躯干出现片状红斑伴脱屑，运动出汗后瘙痒加重，已持续一周。',
      onset_duration: '1 周',
      itch_level: 4,
      pain_level: 2,
      spread_flag: true,
      spread_parts: ['躯干', '手臂'],
      status: 'WAIT_DOCTOR',
      risk_level: 'HIGH',
      submitted_at: '2026-04-21 09:58',
      images: [
        makeSkinShot('#f3d5c6', '#ebb9a6', ['#cf5e5e', '#d34d4d', '#be4044', '#dd6b6b']),
        makeSkinShot('#f1d1bf', '#e9ac9c', ['#c84c4c', '#d06a5d', '#cf5350', '#bf3f47']),
      ],
      ai_result: {
        image_observation: '躯干局部可见边界相对清晰的片状红斑与鳞屑，部分区域呈扩散趋势。',
        risk_level: 'HIGH',
        possible_directions: [
          { label: '湿疹 / 特应性皮炎', value: 40 },
          { label: '银屑病', value: 32 },
          { label: '体癣', value: 16 },
          { label: '药物疹', value: 12 },
        ],
        condition_guess: '广泛炎症性皮损，需要进一步鉴别',
        confidence: 76,
        advice: [
          '避免继续抓挠与热水洗澡，优先保持皮肤干燥透气。',
          '建议尽快补充病史与用药史，由医生判断是否需要线下检查。',
          '若出现渗液、发热或扩散明显，建议立即就医。',
        ],
        alert: '存在高风险扩散信号，建议优先医生处理并关注是否需要线下面诊。',
        recommendation: '建议医生第一时间复核，必要时直接建议线下就医。',
      },
    },
    {
      case_id: 1003,
      case_no: '2026-0621-000130',
      patient_id: 203,
      doctor_id: 301,
      summary_title: '下巴密集丘疹 3 天',
      symptom_summary: '下巴和口周出现密集丘疹，近期熬夜较多，偶有轻微疼痛。',
      onset_duration: '3 天内',
      itch_level: 1,
      pain_level: 2,
      spread_flag: false,
      spread_parts: ['下巴'],
      status: 'DOCTOR_REPLIED',
      risk_level: 'LOW',
      submitted_at: '2026-04-21 09:41',
      images: [
        makeSkinShot('#f7d9cb', '#f1c4b7', ['#e56776', '#db5768', '#f08b93', '#e85a65']),
      ],
      ai_result: {
        image_observation: '口周与下巴可见较密集的炎性丘疹，未见明显囊肿或结节。',
        risk_level: 'LOW',
        possible_directions: [
          { label: '轻中度痤疮', value: 58 },
          { label: '口周皮炎', value: 22 },
          { label: '屏障受损', value: 12 },
          { label: '激素依赖', value: 8 },
        ],
        condition_guess: '轻中度炎症性痤疮',
        confidence: 88,
        advice: [
          '加强晚间清洁与保湿，避免频繁挤压和叠加高浓度酸类。',
          '保持作息规律，连续观察 1 周变化。',
        ],
        alert: '当前为低风险，可先以护理建议为主。',
        recommendation: '医生可补充作息与外用药建议。',
      },
      doctor_reply: {
        first_impression: '更符合轻中度痤疮表现，当前无需过度紧张。',
        care_advice: '建议晚间使用温和清洁与修护乳，避免自行叠加多种祛痘产品。',
        suggest_offline: false,
        suggest_revisit: true,
        note: '若 1 周后仍持续爆发，可考虑线下面诊评估。',
        replied_at: '2026-04-21 11:16',
      },
      ai_feedback: {
        accuracy: 'ACCURATE',
        note: 'AI 对炎症性痤疮方向判断较准确。',
      },
    },
    {
      case_id: 1004,
      case_no: '2026-0620-000121',
      patient_id: 201,
      doctor_id: 301,
      summary_title: '鼻翼脱屑伴灼热感',
      symptom_summary: '鼻翼周围脱屑明显，伴灼热与轻微刺痛。',
      onset_duration: '1 周',
      itch_level: 2,
      pain_level: 2,
      spread_flag: false,
      spread_parts: ['鼻翼'],
      status: 'AI_DONE',
      risk_level: 'MEDIUM',
      submitted_at: '2026-04-20 20:16',
      images: [
        makeSkinShot('#f6dbcf', '#f0bfb4', ['#e1867e', '#dd6f6c', '#eb9a91', '#d56c6a']),
      ],
      ai_result: {
        image_observation: '鼻翼与鼻旁可见片状干燥脱屑，局部轻度潮红，提示屏障受损伴刺激。',
        risk_level: 'MEDIUM',
        possible_directions: [
          { label: '脂溢性皮炎', value: 37 },
          { label: '屏障受损', value: 30 },
          { label: '接触性皮炎', value: 18 },
          { label: '湿疹样反应', value: 15 },
        ],
        condition_guess: '脂溢性皮炎 / 清洁过度',
        confidence: 80,
        advice: [
          '减少清洁频次与高浓度酸类使用，加强保湿。',
          '如灼热感持续加重，建议医生复核。',
        ],
        alert: '中风险，需要观察是否继续扩散到口周。',
        recommendation: '建议补充既往护肤史与是否使用去角质产品。',
      },
    },
    {
      case_id: 1005,
      case_no: '2026-0618-000102',
      patient_id: 204,
      doctor_id: 301,
      summary_title: '眼周闭口和刺痛 1 月',
      symptom_summary: '眼周反复出现闭口，偶尔伴轻微刺痛，使用某款防晒后加重。',
      onset_duration: '1 月',
      itch_level: 1,
      pain_level: 1,
      spread_flag: false,
      spread_parts: ['眼周'],
      status: 'CLOSED',
      risk_level: 'LOW',
      submitted_at: '2026-04-18 19:32',
      images: [
        makeSkinShot('#f7ded4', '#f2cabc', ['#e0aa9f', '#d98b85', '#efc1b7']),
      ],
      ai_result: {
        image_observation: '眼周区域可见轻度闭口样突起，无明显炎症红肿。',
        risk_level: 'LOW',
        possible_directions: [
          { label: '闭口粉刺', value: 48 },
          { label: '刺激后堵塞', value: 31 },
          { label: '脂肪粒', value: 12 },
          { label: '轻度接触反应', value: 9 },
        ],
        condition_guess: '轻度闭口粉刺',
        confidence: 86,
        advice: ['减少厚重防晒与眼周叠加产品，保持轻量保湿。'],
        alert: '暂无高风险提示。',
        recommendation: '可继续居家护理观察。',
      },
      doctor_reply: {
        first_impression: '目前风险较低，更像是产品堆叠带来的闭口问题。',
        care_advice: '暂停相关防晒，简化眼周护理 1-2 周。',
        suggest_offline: false,
        suggest_revisit: false,
        note: '如果出现持续刺痛或红肿，再进一步复查。',
        replied_at: '2026-04-19 08:20',
      },
      ai_feedback: {
        accuracy: 'PARTIAL',
        note: 'AI 对闭口方向准确，但对刺激史利用不足。',
      },
    },
    {
      case_id: 1006,
      case_no: '2026-0617-000095',
      patient_id: 205,
      doctor_id: 301,
      summary_title: '面部干燥脱皮 5 天',
      symptom_summary: '近期频繁使用去角质产品后面部干燥脱皮，洗脸后刺痛。',
      onset_duration: '5 天',
      itch_level: 2,
      pain_level: 3,
      spread_flag: true,
      spread_parts: ['面部', '鼻翼'],
      status: 'WAIT_DOCTOR',
      risk_level: 'MEDIUM',
      submitted_at: '2026-04-21 08:55',
      images: [
        makeSkinShot('#f7dccf', '#efc2b3', ['#d67c74', '#cf6768', '#e8aa9a', '#e18d89']),
      ],
      ai_result: {
        image_observation: '面部可见广泛干燥脱屑，提示屏障受损，局部伴刺激性潮红。',
        risk_level: 'MEDIUM',
        possible_directions: [
          { label: '屏障受损', value: 51 },
          { label: '刺激性皮炎', value: 28 },
          { label: '脂溢性皮炎', value: 11 },
          { label: '湿疹', value: 10 },
        ],
        condition_guess: '去角质过度导致的屏障受损',
        confidence: 84,
        advice: [
          '立即停止去角质和酸类产品，优先修护保湿。',
          '避免热水、磨砂和频繁清洁。',
        ],
        alert: '若刺痛持续增强，需评估是否存在更明显炎症反应。',
        recommendation: '建议医生补充修护方案和复查建议。',
      },
    },
  ],
  configs: [
    {
      config_key: 'prompt_version',
      title: 'Prompt 模板版本',
      description: '当前医生端与 AI 分析协同使用的模板版本。',
      config_value: 'v2.6.0',
      type: 'text',
    },
    {
      config_key: 'doctor_review_enabled',
      title: '医生复核开关',
      description: '开启后，高风险或中风险案例默认进入医生复核。',
      config_value: true,
      type: 'switch',
    },
    {
      config_key: 'upload_limit_mb',
      title: '文件上传限制',
      description: '用户端单次上传图片总大小限制。',
      config_value: 20,
      type: 'number',
    },
    {
      config_key: 'followup_window_hours',
      title: '复查提醒窗口',
      description: '医生建议复查后的默认提醒时长。',
      config_value: 72,
      type: 'number',
    },
  ],
  operationLogs: [
    {
      log_id: 1,
      operator: '管理员',
      module_name: '系统配置',
      operation_type: '更新',
      operation_desc: '调整医生复核开关与复查提醒窗口。',
      created_at: '2026-04-21 14:30:12',
      result: 'SUCCESS',
    },
    {
      log_id: 2,
      operator: '管理员',
      module_name: '文本问答',
      operation_type: '上传',
      operation_desc: '上传痤疮诊疗指南（2025 更新）。',
      created_at: '2026-04-21 14:20:10',
      result: 'SUCCESS',
    },
    {
      log_id: 3,
      operator: '张晓雨',
      module_name: '问诊回复',
      operation_type: '提交',
      operation_desc: '完成病例 2026-0621-000130 医生回复。',
      created_at: '2026-04-21 11:16:36',
      result: 'SUCCESS',
    },
    {
      log_id: 4,
      operator: '管理员',
      module_name: '医生管理',
      operation_type: '审核',
      operation_desc: '将刘桐医生服务状态切换为暂停。',
      created_at: '2026-04-21 10:42:08',
      result: 'SUCCESS',
    },
    {
      log_id: 5,
      operator: '系统',
      module_name: '风险预警',
      operation_type: '通知',
      operation_desc: '高风险案例 2026-0621-000129 推送医生优先处理。',
      created_at: '2026-04-21 09:59:44',
      result: 'SUCCESS',
    },
  ],
  modelLogs: [
    {
      log_id: 1,
      biz_type: '图文问诊',
      model_name: 'GPT-4.1 Vision',
      duration: '2.1 s',
      token_cost: '3,520',
      created_at: '2026-04-21 10:24:18',
      status: 'SUCCESS',
      summary: '完成面部泛红案例图像观察与风险级别评估。',
    },
    {
      log_id: 2,
      biz_type: '联网搜索问答',
      model_name: 'GPT-4.1 Mini',
      duration: '1.4 s',
      token_cost: '1,280',
      created_at: '2026-04-21 10:02:11',
      status: 'SUCCESS',
      summary: '调用 Tavily 检索公开资料并生成最新问答回复。',
    },
    {
      log_id: 3,
      biz_type: '图文问诊',
      model_name: 'GPT-4.1 Vision',
      duration: '2.8 s',
      token_cost: '4,106',
      created_at: '2026-04-21 09:58:23',
      status: 'RETRY',
      summary: '首次返回图像特征不完整，系统执行二次补全。',
    },
    {
      log_id: 4,
      biz_type: '医生辅助',
      model_name: 'GPT-4.1',
      duration: '1.9 s',
      token_cost: '2,030',
      created_at: '2026-04-21 09:41:28',
      status: 'SUCCESS',
      summary: '生成医生回复推荐草稿。',
    },
  ],
  announcements: [
    {
      announcement_id: 1,
      title: '医生端高风险复核流程已升级',
      content: '高风险问诊现已自动进入优先队列，医生工作台会展示风险预警和 AI 参考摘要。',
      scope: 'DOCTOR',
      created_at: '2026-04-21 12:30',
    },
    {
      announcement_id: 2,
      title: '文本问答已支持联网检索',
      content: '用户端文本问答现已支持按需联网搜索公开资料，并展示来源链接。',
      scope: 'ALL',
      created_at: '2026-04-21 11:42',
    },
    {
      announcement_id: 3,
      title: '图片上传大小限制调整为 20MB',
      content: '为保证移动端上传体验和模型稳定性，单次上传图片总大小限制调整为 20MB。',
      scope: 'USER',
      created_at: '2026-04-20 17:20',
    },
  ],
}

function readState(): ControlCenterState {
  if (typeof window === 'undefined') {
    return clone(mockStateSeed)
  }

  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    const initial = clone(mockStateSeed)
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(initial))
    return initial
  }

  try {
    return JSON.parse(raw) as ControlCenterState
  } catch {
    const initial = clone(mockStateSeed)
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(initial))
    return initial
  }
}

function writeState(state: ControlCenterState) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }
}

function mutateState<T>(handler: (state: ControlCenterState) => T): T {
  const state = readState()
  const result = handler(state)
  writeState(state)
  return result
}

function formatDelta(current: number, previous: number) {
  if (!previous) {
    return '+0%'
  }
  const delta = ((current - previous) / previous) * 100
  return `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`
}

function previousTotals(total: number) {
  return Math.max(Math.round(total * 0.92), 1)
}

function enrichConsultation(state: ControlCenterState, item: ConsultationRecord) {
  const patient = state.patients.find((entry) => entry.patient_id === item.patient_id)!
  const doctor = state.doctors.find((entry) => entry.doctor_id === item.doctor_id)!
  return {
    ...clone(item),
    patient: clone(patient),
    doctor: clone(doctor),
  }
}

function buildTrendSeries(state: ControlCenterState) {
  const counts = [18, 24, 32, 29, 38, 34, state.consultations.length * 7]
  const riskCounts = [4, 5, 5, 6, 7, 6, state.consultations.filter((item) => item.risk_level === 'HIGH').length * 2]
  return ['04-15', '04-16', '04-17', '04-18', '04-19', '04-20', '04-21'].map((label, index) => ({
    label,
    consultations: counts[index],
    highRisk: riskCounts[index],
  }))
}

function buildAccuracy(state: ControlCenterState) {
  const feedback = state.consultations
    .map((item) => item.ai_feedback?.accuracy)
    .filter(Boolean) as Array<'ACCURATE' | 'PARTIAL' | 'INACCURATE'>
  if (!feedback.length) {
    return 0
  }

  const score = feedback.reduce((sum, item) => {
    if (item === 'ACCURATE') return sum + 1
    if (item === 'PARTIAL') return sum + 0.6
    return sum + 0.2
  }, 0)

  return Number(((score / feedback.length) * 100).toFixed(1))
}

export async function loginControlCenter(username: string, password: string) {
  const accounts = [doctorAccount, adminAccount]
  const found = accounts.find((item) => item.username === username)
  if (!found || password !== '12345678') {
    throw new Error('账号或密码错误，请使用演示账号登录。')
  }

  return {
    access_token: `mock-${found.role_type.toLowerCase()}-${Date.now()}`,
    account: clone(found),
  }
}

export async function getDoctorWorkspace() {
  const state = readState()
  const consultations = state.consultations
    .slice()
    .sort((first, second) => second.submitted_at.localeCompare(first.submitted_at))
    .map((item) => enrichConsultation(state, item))

  const pending = consultations.filter((item) => item.status === 'WAIT_DOCTOR')
  const replied = consultations.filter((item) => item.status === 'DOCTOR_REPLIED')
  const highRisk = consultations.filter((item) => item.risk_level === 'HIGH')
  const accuracy = buildAccuracy(state)

  return {
    doctor: clone(state.doctors[0]),
    metrics: [
      { label: '待处理问诊', value: pending.length, change: '+6', accent: 'violet' },
      { label: '今日已处理', value: replied.length + 6, change: '+12', accent: 'blue' },
      { label: '高风险预警', value: highRisk.length, change: '+2', accent: 'rose' },
      { label: 'AI 反馈准确率', value: `${accuracy}%`, change: '+1.8%', accent: 'mint' },
    ],
    queue: consultations,
    alerts: highRisk.slice(0, 3),
    focusCase: consultations[0],
    trend: buildTrendSeries(state),
    replyTemplates: [
      '建议暂停近期新增护肤品，优先观察刺激是否减轻。',
      '若 48 小时内继续扩散或出现渗液，请建议线下面诊。',
      '若仅局部轻度发红，可先以修护与观察为主。',
    ],
  }
}

export async function getDoctorPatients() {
  const state = readState()
  return state.patients.map((patient) => ({
    ...clone(patient),
    recentCases: patient.recent_case_ids.map((id) => enrichConsultation(state, state.consultations.find((item) => item.case_id === id)!)),
  }))
}

export async function getDoctorConsultationList() {
  const state = readState()
  return state.consultations
    .slice()
    .sort((first, second) => second.submitted_at.localeCompare(first.submitted_at))
    .map((item) => enrichConsultation(state, item))
}

export async function getDoctorConsultation(caseId: number) {
  const state = readState()
  const item = state.consultations.find((entry) => entry.case_id === caseId)
  return item ? enrichConsultation(state, item) : null
}

export async function saveDoctorReply(caseId: number, payload: DoctorReplyPayload) {
  mutateState((state) => {
    const target = state.consultations.find((item) => item.case_id === caseId)
    if (!target) return
    target.doctor_reply = {
      ...payload,
      replied_at: '2026-04-21 15:08',
    }
    target.status = 'DOCTOR_REPLIED'
  })
}

export async function saveDoctorAiFeedback(caseId: number, payload: FeedbackPayload) {
  mutateState((state) => {
    const target = state.consultations.find((item) => item.case_id === caseId)
    if (!target) return
    target.ai_feedback = clone(payload)
  })
}

export async function getAdminWorkspace() {
  const state = readState()
  const consultations = state.consultations
  const highRisk = consultations.filter((item) => item.risk_level === 'HIGH').length
  const aiCalls = consultations.length * 27 + 93
  const webSearchCalls = state.modelLogs.filter((item) => item.biz_type === '联网搜索问答').length * 128 + 43
  const metrics = [
    { label: '用户总数', value: state.users.length * 2489, change: formatDelta(state.users.length * 2489, previousTotals(state.users.length * 2489)), accent: 'blue' },
    { label: '医生总数', value: state.doctors.length * 251, change: formatDelta(state.doctors.length * 251, previousTotals(state.doctors.length * 251)), accent: 'violet' },
    { label: '问诊总量', value: consultations.length * 8112, change: formatDelta(consultations.length * 8112, previousTotals(consultations.length * 8112)), accent: 'sky' },
    { label: 'AI 调用次数', value: aiCalls, change: '+15.7%', accent: 'mint' },
    { label: '联网问答次数', value: webSearchCalls, change: '+14.1%', accent: 'lilac' },
    { label: '高风险问诊量', value: highRisk * 88, change: '+7.8%', accent: 'rose' },
  ]

  return {
    metrics,
    users: clone(state.users),
    doctors: clone(state.doctors),
    consultations: state.consultations.map((item) => enrichConsultation(state, item)),
    configs: clone(state.configs),
    operationLogs: clone(state.operationLogs),
    modelLogs: clone(state.modelLogs),
    announcements: clone(state.announcements),
    trend: buildTrendSeries(state),
  }
}

export async function updateUserStatus(accountId: number, status: 0 | 1) {
  mutateState((state) => {
    const target = state.users.find((item) => item.account_id === accountId)
    if (target) {
      target.status = status
    }
  })
}

export async function auditDoctor(doctorId: number, auditStatus: AuditStatus) {
  mutateState((state) => {
    const target = state.doctors.find((item) => item.doctor_id === doctorId)
    if (target) {
      target.audit_status = auditStatus
    }
  })
}

export async function toggleDoctorService(doctorId: number) {
  mutateState((state) => {
    const target = state.doctors.find((item) => item.doctor_id === doctorId)
    if (target) {
      target.service_status = target.service_status === 1 ? 0 : 1
    }
  })
}

export async function updateConfig(configKey: string, configValue: ConfigRecord['config_value']) {
  mutateState((state) => {
    const target = state.configs.find((item) => item.config_key === configKey)
    if (target) {
      target.config_value = configValue
    }
  })
}

export async function publishAnnouncement(payload: AnnouncementPayload) {
  mutateState((state) => {
    state.announcements.unshift({
      announcement_id: Date.now(),
      title: payload.title,
      content: payload.content,
      scope: payload.scope,
      created_at: '2026-04-21 15:20',
    })
  })
}

export function getConsultationStatusLabel(status: ConsultationStatus) {
  return {
    WAIT_DOCTOR: '待医生处理',
    AI_DONE: 'AI 已完成',
    DOCTOR_REPLIED: '医生已回复',
    CLOSED: '已关闭',
  }[status]
}

export function getRiskLabel(risk: ConsultationRisk) {
  return {
    LOW: '低风险',
    MEDIUM: '中风险',
    HIGH: '高风险',
  }[risk]
}
