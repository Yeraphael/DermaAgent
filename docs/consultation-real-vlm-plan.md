# DermaAgent 图文智能问诊真实视觉大模型接入方案

## 1. 目标

本方案面向当前 `http://127.0.0.1:5174/#/consultation` 的 H5 用户端，完成从“高保真 demo”到“真实图文智能问诊模块”的落地设计，并兼容现有小程序页。

目标不是只把一个模型 API 调通，而是完成一条可上线、可追踪、可回退的真实业务链路：

1. 用户登录真实账号。
2. 用户上传皮肤图片与症状描述。
3. 前端调用后端真实问诊接口。
4. 后端调用真实视觉大模型生成结构化分析结果。
5. 分析结果入库、可追踪、可在分析页/历史页/医生端复用。
6. 高风险病例自动进入医生复核流转。

## 2. 现状评估

### 2.1 前端现状

当前 H5 `#/consultation` 页面并没有接真实接口，仍然依赖本地 mock 状态：

- `apps/mobile-user/src/views/ConsultationView.vue`
  页面提交调用的是 `submitPortalConsultation(...)`。
- `apps/mobile-user/src/views/AnalysisView.vue`
  分析页读取的是 `getPortalConsultation(...)` 和 `getPortalConsultations()`。
- `apps/mobile-user/src/views/LoginView.vue`
  登录调用的是 `loginPortalUser(...)`，不是后端 `/auth/login`。
- `apps/mobile-user/src/shared/portal.ts`
  整个用户端 H5 的登录、问诊、分析、问答、通知都还是本地假数据。

同时，小程序页也还没有走真实接口：

- `apps/mobile-user/src/pages/consultation/index.vue`
  同样调用 `submitPortalConsultation(...)`。

### 2.2 后端现状

后端已经具备一部分基础能力，但还没有到“真实生产链路”：

- `backend/app/routes/common.py`
  已有图片上传接口 `/files/upload-image`。
- `backend/app/routes/consultation.py`
  已有问诊创建接口 `/consultations`、详情接口、消息接口。
- `backend/app/ai.py`
  已有 `VisualAnalyzer`，支持 `mock` 和 `real` 两种模式。
- `backend/app/config.py`
  已预留 `AI_MODE`、`QWEN_API_KEY`、`QWEN_BASE_URL`、`QWEN_VISUAL_MODEL`。
- `.env.example`
  默认已经指向兼容模式网关：`https://dashscope.aliyuncs.com/compatible-mode/v1`。

### 2.3 当前主要缺口

当前还缺少下面这些关键能力：

1. H5 和小程序前端没有切到真实登录、真实上传、真实问诊、真实分析结果展示。
2. H5 分析页展示结构仍是 mock 格式，和后端 `ai_result` 返回结构不一致。
3. 视觉模型调用虽然有骨架，但缺少严格的 JSON 输出约束、失败重试、结果校验、日志追踪和超时降级。
4. 图片上传缺少尺寸、大小、数量、内容安全、去重和压缩策略。
5. 问诊数据没有保存 `spreadParts`，前端采集了，但后端 schema/model 没有接住。
6. AI 分析记录表字段偏少，缺少 provider、耗时、token、请求 ID、失败原因细分等观测字段。
7. 目前创建问诊时同步调用 AI，若模型耗时升高，会直接拖慢接口体验。
8. 没有形成“高风险自动医生复核”的清晰规则闭环。

## 3. 推荐落地路线

建议采用“保留现有后端接口骨架，替换前端 mock 层，增强后端模型编排”的路线，而不是推翻重做。

原因：

1. 你现在的后端路由、数据库表、医生分配、通知、历史记录已经有雏形。
2. `backend/app/ai.py` 已经按“兼容 OpenAI 风格 chat completions”的方式预留了真实调用入口。
3. 继续沿用这条路线，改动面集中、成本最低、最适合毕业设计项目推进。

## 4. 总体架构方案

### 4.1 端到端链路

```text
H5/小程序 consultation 页
  -> 登录鉴权
  -> 上传 1~5 张图片
  -> 提交问诊表单
  -> 后端创建 consultation
  -> 后端调用视觉大模型
  -> 结构化解析与风控判断
  -> AIAnalysisRecord 入库
  -> consultation 状态更新
  -> 前端跳转 analysis 详情页
  -> 历史页/医生端复用同一份结果
```

### 4.2 模块分层

建议拆成 4 层：

1. 前端页面层
   H5 与小程序提交问诊、展示分析结果。
2. 前端 API 层
   统一调用后端接口，不再直接操作 `shared/portal.ts`。
3. 后端业务层
   创建问诊、拼接健康档案、触发 AI、持久化结果、生成通知。
4. AI Provider 层
   只负责与具体视觉模型厂商交互，屏蔽供应商差异。

## 5. 前端改造方案

## 5.1 H5 端改造重点

H5 当前真实入口是：

- `apps/mobile-user/src/views/LoginView.vue`
- `apps/mobile-user/src/views/ConsultationView.vue`
- `apps/mobile-user/src/views/AnalysisView.vue`

建议新增真实 API 服务文件，例如：

- `apps/mobile-user/src/services/auth.ts`
- `apps/mobile-user/src/services/consultation.ts`
- `apps/mobile-user/src/services/upload.ts`

### H5 需要完成的改造

1. 登录页切换到 `/auth/login`。
2. 上传图片改为先调 `/files/upload-image`，获取 `file_url`。
3. 提交问诊改为调 `/consultations`。
4. 分析页改为调 `/consultations/{case_id}` 获取真实详情。
5. 历史页改为调 `/consultations/my`。
6. 逐步下线 `shared/portal.ts` 在 H5 里的问诊、分析、登录 mock 能力。

### H5 页面字段映射

`ConsultationView.vue` 当前表单字段与后端基本能对上：

- `description` -> `chief_complaint`
- `onsetDuration` -> `onset_duration`
- `itchLevel` -> `itch_level`
- `painLevel` -> `pain_level`
- `spreadFlag` -> `spread_flag`
- `previews / files` -> 先上传，再转成 `image_urls`

但还需要补一个字段：

- `spreadParts` -> 建议后端新增 `spread_parts`

## 5.2 小程序端改造重点

对应文件：

- `apps/mobile-user/src/pages/consultation/index.vue`

小程序端的改造逻辑和 H5 相同，只是上传和导航方式不同：

1. `uni.chooseImage` 获取本地文件。
2. `uni.uploadFile` 上传到 `/files/upload-image`。
3. 汇总 `file_url` 后调 `/consultations`。
4. 提交成功后跳转 `/pages/analysis/index?caseId=xxx`。

建议让 H5 和小程序共享同一套业务 service，只在“文件选择 / 上传适配器”层做平台区分。

## 5.3 前端返回结构统一

当前 H5 分析页使用的是 portal mock 结构：

- `detail.ai.observation`
- `detail.ai.directions`
- `detail.ai.careAdvice`
- `detail.ai.shouldVisit`

后端实际返回的是：

- `ai_result.image_observation`
- `ai_result.possible_conditions`
- `ai_result.care_advice`
- `ai_result.hospital_advice`
- `ai_result.high_risk_alert`
- `ai_result.risk_level`

建议前端新增一层 DTO 适配，把后端结果转换成前端展示模型，例如：

```ts
type ConsultationDetailViewModel = {
  caseId: number
  caseNo: string
  title: string
  description: string
  visuals: string[]
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
  ai: {
    observation: string
    possibleConditions: string[]
    careAdvice: string[]
    hospitalAdvice: string
    highRiskAlert: string
    disclaimer: string
  }
}
```

这样前端视图就不会和后端数据库字段直接耦合。

## 6. 后端改造方案

## 6.1 保留现有接口，增强实现

现有接口建议保留：

- `POST /api/v1/auth/login`
- `POST /api/v1/files/upload-image`
- `POST /api/v1/consultations`
- `GET /api/v1/consultations/my`
- `GET /api/v1/consultations/{case_id}`

重点是增强 `POST /consultations` 的真实业务链路。

## 6.2 Consultation 入参增强

当前 `backend/app/schema.py` 中 `ConsultationCreateIn` 为：

- `chief_complaint`
- `onset_duration`
- `itch_level`
- `pain_level`
- `spread_flag`
- `need_doctor_review`
- `image_urls`

建议新增：

1. `spread_parts: list[str] = []`
2. `client_platform: str | None = None`
3. `extra_context: str | None = None`

其中 `spread_parts` 是当前前端已经采集但尚未持久化的字段。

## 6.3 Consultation 表建议补字段

当前 `backend/app/model.py` 的 `Consultation` 表还不够承载完整问诊上下文。

建议新增字段：

1. `spread_parts`：`Text`，存 JSON 字符串。
2. `source_platform`：`String(20)`，记录 `H5 / MP_WEIXIN / WEB`。
3. `ai_status`：`String(20)`，与业务状态分开，取值如 `PENDING/RUNNING/SUCCESS/FAILED/FALLBACK`。
4. `ai_provider`：`String(50)`，记录本次使用的模型供应商。
5. `triage_level`：`String(20)`，独立记录问诊分级。

说明：

- 现在 `status` 混合了承载“业务流转状态”和“AI 执行状态”，后期会越来越难维护。
- 最好把“问诊流转状态”和“AI 执行状态”拆开。

## 6.4 AIAnalysisRecord 表建议补字段

当前 `AIAnalysisRecord` 已有文本结果，但缺少可运维字段。

建议新增：

1. `provider_name`
2. `provider_request_id`
3. `provider_status_code`
4. `latency_ms`
5. `request_tokens`
6. `response_tokens`
7. `finish_reason`
8. `parsed_json`
9. `input_images_json`
10. `fail_stage`

这样后面遇到“模型慢、结果空、解析失败、厂商限流、账单异常”时，才能真正定位。

## 6.5 AI Provider 抽象

建议不要把所有调用逻辑都堆在 `backend/app/ai.py` 的一个类里，而是拆成：

1. `backend/app/ai/base.py`
   定义统一返回结构和 provider 接口。
2. `backend/app/ai/providers/qwen_vl.py`
   封装千问视觉模型调用。
3. `backend/app/ai/prompts/consultation_prompt.py`
   管理系统提示词和输出 JSON 模式。
4. `backend/app/ai/parser.py`
   负责 JSON 校验、字段补齐、兜底解析。

如果现在项目时间紧，至少也建议在现有 `backend/app/ai.py` 内做“类内分层”。

## 6.6 模型调用策略

建议继续沿用当前项目已经预留的“兼容 OpenAI chat completions 协议”的方式，不改供应商接入方式，只增强协议细节。

建议调用策略：

1. `temperature=0.1 ~ 0.2`
   降低输出漂移。
2. 限制最大输出长度。
3. 强制返回 JSON。
4. 设置超时，例如 30s。
5. 至少一次重试，但只对超时/网络错误重试，不对 4xx 业务错误重试。
6. 失败时记录失败原因，并返回“可解释降级结果”。

## 6.7 提示词与输出格式设计

当前 `backend/app/ai.py` 的 system prompt 太简单，只说“输出 JSON”，约束不够强。

建议视觉模型返回固定结构：

```json
{
  "prompt_version": "consultation-v1",
  "image_observation": "string",
  "possible_conditions": ["string", "string", "string"],
  "risk_level": "LOW|MEDIUM|HIGH",
  "care_advice": ["string", "string", "string"],
  "hospital_advice": "string",
  "high_risk_alert": "string",
  "doctor_review_needed": true,
  "confidence": 0.0,
  "disclaimer": "string"
}
```

建议 system prompt 明确限制：

1. 不允许输出最终医学确诊。
2. 只能输出辅助观察、风险分层、护理建议、就医提醒。
3. 一律使用中文。
4. 一律返回 JSON，不得附带 Markdown。
5. 遇到图片不清晰、信息不足时必须说明“不足以判断”。

## 6.8 图片处理策略

当前上传接口只校验扩展名，还不够。

建议增强 `/files/upload-image`：

1. 校验 MIME type。
2. 限制单图大小，例如 8MB。
3. 限制分辨率上限，必要时自动压缩。
4. 自动转为统一格式，例如 JPEG/WebP。
5. 去除 EXIF 中的地理信息。
6. 限制最多上传 5 张。
7. 对模糊图、纯黑图、过曝图做基础质量判断。

原因：

- 视觉模型效果高度依赖图片质量。
- 医疗图片属于敏感数据，元数据脱敏很重要。

## 6.9 同步还是异步

### MVP 阶段建议

第一版可以继续同步调用 AI，这样改动最小，链路最短。

同步方案要求：

1. 30 秒内大概率返回。
2. 前端有 loading 态。
3. 超时后给出“已受理，稍后生成结果”的兜底提示。

### 第二阶段建议

中期建议改成异步：

1. `POST /consultations` 先创建病例，返回 `case_id`。
2. 后台任务处理 AI 分析。
3. 前端轮询 `GET /consultations/{case_id}` 或通过 websocket/sse 等待状态变化。

异步更适合真实模型，因为模型响应时间、供应商限流和高峰波动都更大。

## 7. 风险分层与医生复核规则

建议把“AI 风险分层”和“是否转医生复核”写成明确规则，不要只靠模型自由发挥。

### 7.1 AI 输出层

模型给出：

- `risk_level`
- `doctor_review_needed`
- `confidence`

### 7.2 业务规则层

后端二次判定：

1. `risk_level == HIGH` 时，强制 `WAIT_DOCTOR`。
2. 出现关键词如“渗液、发热、破溃、迅速扩散、明显疼痛”时，强制 `WAIT_DOCTOR`。
3. 图片质量差或字段缺失时，也建议医生复核。
4. `confidence` 低于阈值时，不直接放行 AI_DONE。

这一步非常关键，因为医疗场景不能完全把分流逻辑交给模型自由生成。

## 8. 数据安全与合规建议

这是图文医疗问诊模块，至少需要做到项目级安全控制：

1. 图片上传路径按业务目录隔离。
2. 访问图片时尽量不要永久公网暴露，后期可改签名 URL。
3. 对 `raw_response` 做访问控制，仅医生/管理员可见完整内容。
4. 结果页必须显示免责声明。
5. 日志里避免打印用户原始图片 URL、完整健康档案和完整模型响应。
6. 若项目需要演示答辩，可准备“脱敏模式”截图。

## 9. 建议的接口数据流

## 9.1 提交问诊

前端流程：

1. 用户选择图片。
2. 前端逐张上传 `/files/upload-image`。
3. 收集返回的 `file_url`。
4. 调用 `/consultations`。

请求示例：

```json
{
  "chief_complaint": "面部泛红伴瘙痒，近两天加重，洗脸后刺痛",
  "onset_duration": "2天内",
  "itch_level": 3,
  "pain_level": 2,
  "spread_flag": 1,
  "spread_parts": ["面部", "鼻翼"],
  "need_doctor_review": 1,
  "image_urls": [
    "http://127.0.0.1:8000/uploads/consultation/20260428120000-1-12345.jpg"
  ],
  "client_platform": "H5"
}
```

## 9.2 提交成功返回

建议直接返回：

1. `consultation`
2. `ai_result`
3. `triage`

这样前端可以直接跳到分析页，也能在提交成功页展示摘要。

## 9.3 查询详情

`GET /consultations/{case_id}` 返回结构建议保持当前风格，但补齐：

1. `spread_parts`
2. `ai_status`
3. `triage_level`
4. `doctor_review_needed`
5. `image_quality_notes`

## 10. 具体文件改动清单

下面是我建议你实际改动的第一批文件。

### 前端

- `apps/mobile-user/src/views/LoginView.vue`
  从 `loginPortalUser` 改为真实登录。
- `apps/mobile-user/src/views/ConsultationView.vue`
  从 `submitPortalConsultation` 改为真实上传 + 真实提交。
- `apps/mobile-user/src/views/AnalysisView.vue`
  从 portal mock 数据改为请求后端详情。
- `apps/mobile-user/src/views/HistoryView.vue`
  从 portal mock 改为 `/consultations/my`。
- `apps/mobile-user/src/pages/consultation/index.vue`
  小程序页切换到真实接口。
- `apps/mobile-user/src/pages/analysis/index.vue`
  小程序分析页切换到真实详情接口。
- `apps/mobile-user/src/shared/portal.ts`
  保留演示数据可以，但应逐步退出真实业务链路。
- `apps/mobile-user/src/services/api.ts`
  扩展请求方法和错误处理。

### 后端

- `backend/app/schema.py`
  扩充 `ConsultationCreateIn`。
- `backend/app/model.py`
  扩充 `Consultation` 和 `AIAnalysisRecord`。
- `backend/app/routes/common.py`
  增强上传校验。
- `backend/app/routes/consultation.py`
  增强创建问诊逻辑与返回结构。
- `backend/app/service.py`
  增强 AI 结果持久化、风险规则、详情组装。
- `backend/app/ai.py`
  重构为可维护的真实视觉模型调用层。
- `.env.example`
  补充 AI 相关说明项。

## 11. 分阶段实施计划

## 阶段 1：打通真实最小链路

目标：让 `5174/#/consultation` 真实可用。

任务：

1. H5 登录切换真实 `/auth/login`。
2. H5 图片上传切换真实 `/files/upload-image`。
3. H5 问诊提交切换真实 `/consultations`。
4. H5 分析页切换真实 `/consultations/{id}`。
5. 让后端 `AI_MODE=real` 时走真实视觉模型。
6. 补强 prompt 和 JSON 解析。

交付结果：

1. 用户可以真实登录。
2. 用户可以真实上传图片并得到 AI 结果。
3. 结果能入库、能在分析页查看。

## 阶段 2：补齐结构化与稳定性

任务：

1. 增加 `spread_parts`。
2. 增加 AI 调用日志字段。
3. 增加失败重试与降级。
4. 增加图片质量校验。
5. 增加医生复核规则。

交付结果：

1. 问诊数据完整。
2. AI 可追踪、可排错。
3. 高风险流转稳定。

## 阶段 3：优化体验与异步化

任务：

1. 问诊创建与 AI 分析异步解耦。
2. 增加前端“分析生成中”状态。
3. 历史记录、通知、医生端复用同一结果。
4. 优化分析页展示结构。

交付结果：

1. 用户体验更稳定。
2. 模型慢时系统不会卡死。

## 12. 测试方案

## 12.1 功能测试

1. 正常提交 1 张图片。
2. 正常提交 5 张图片。
3. 无图片提交。
4. 无描述提交。
5. 上传超大图片。
6. 上传错误格式文件。
7. 模型超时。
8. 模型返回非 JSON。
9. 模型返回缺字段。
10. 高风险病例自动转医生复核。

## 12.2 接口测试

重点验证：

1. `/auth/login`
2. `/files/upload-image`
3. `/consultations`
4. `/consultations/my`
5. `/consultations/{case_id}`

## 12.3 页面联调测试

至少覆盖：

1. `#/login`
2. `#/consultation`
3. `#/analysis/:caseId`
4. `#/history`

## 13. 验收标准

当下面条件全部满足时，可以认为“用户图文智能问诊模块”基本完成：

1. `http://127.0.0.1:5174/#/consultation` 不再使用 portal mock 提交问诊。
2. 用户可以真实上传图片并成功创建问诊。
3. 后端可调用真实视觉大模型返回结构化结果。
4. 分析结果可落库并在详情页展示。
5. 高风险病例可自动标记并进入医生复核。
6. 历史页可以看到真实问诊记录。
7. 模型失败时系统不会直接崩溃，能给出可解释兜底。

## 14. 我给你的最终建议

如果你现在要尽快把“实际工作”做出来，最优先顺序建议是：

1. 先把 H5 登录、上传、提交、分析页全部切到真实后端。
2. 再把 `backend/app/ai.py` 从“简单真实调用”升级为“严格 JSON + 可追踪 + 可降级”的版本。
3. 再补 `spread_parts`、AI 日志字段、图片质量校验。
4. 最后再做异步化和体验优化。

换句话说，第一步不是“继续做页面”，而是“拆掉 `shared/portal.ts` 在问诊主链路里的 mock 角色”，这是这次改造的真正起点。

---

文档基于当前仓库结构编写，重点参照了这些文件：

- `apps/mobile-user/src/views/ConsultationView.vue`
- `apps/mobile-user/src/views/AnalysisView.vue`
- `apps/mobile-user/src/views/LoginView.vue`
- `apps/mobile-user/src/pages/consultation/index.vue`
- `apps/mobile-user/src/shared/portal.ts`
- `backend/app/routes/consultation.py`
- `backend/app/routes/common.py`
- `backend/app/ai.py`
- `backend/app/service.py`
- `backend/app/schema.py`
- `backend/app/model.py`
- `backend/app/config.py`
