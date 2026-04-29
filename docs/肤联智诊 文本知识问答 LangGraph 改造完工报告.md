# 肤联智诊 文本知识问答 LangGraph 改造完工报告

> 完工日期：2026-04-29  
> 改造范围：用户文本知识问答、LangGraph 轻量流程、Tavily 联网搜索、历史保存、RAG 相关后端删除、管理员前端清理与页面优化

---

## 1. 本次交付结论

本次已经按《文本知识问答与 LangGraph 多轮对话改造：需求与实施计划》完成第一版轻量改造，并明确遵循“不做复杂 Agent、只做必要四件事”的要求：

1. 路由；
2. 直接回答；
3. Tavily 搜索回答；
4. 历史保存。

同时，原有 RAG 知识库后端链路已经从运行时路径中移除，管理员端知识库相关前端入口也已删除并完成文案与页面调整。

---

## 2. 实际完成内容

### 2.1 后端能力改造

已将旧的 RAG 文本问答替换为基于 LangGraph 的轻量多轮对话流程：

- `load_history`
- `router`
- `direct_answer`
- `tavily_search`
- `tool_answer`
- `save_message`

当前支持的意图类型：

- `DIRECT_ANSWER`
- `WEB_SEARCH`
- `CLARIFY`
- `SYSTEM_HELP`
- `MEDICAL_RISK`

但流程分支刻意保持轻量，只保留两条实际执行链路：

- 直接回答链路
- Tavily 搜索增强回答链路

### 2.2 已新增的聊天能力

新增接口：

- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}/messages`
- `POST /api/v1/chat/sessions/{session_id}/messages`

新增数据表模型：

- `chat_sessions`
- `chat_messages`
- `tool_call_logs`

聊天记录支持：

- 会话创建
- 多轮上下文问答
- 用户消息与助手消息持久化
- Tavily 调用日志记录
- 来源列表返回给前端展示

### 2.3 RAG 后端删除情况

已从运行时代码中删除或移除旧 RAG 逻辑：

- 删除 `backend/app/rag.py`
- 删除旧 `/rag/qa` 接口链路
- 删除管理员知识文档接口
- 删除后端配置中的 Qdrant / RAG 运行参数
- 删除知识文档与知识切片相关 ORM 模型

说明：

- 为避免误删用户现有数据库内容，本次没有自动执行线上旧表物理删除。
- 也就是说，运行时代码已经不再依赖旧 RAG 表，但数据库中若仍保留历史旧表，属于“保留但不再使用”状态。

### 2.4 管理员前端清理

管理员端已完成以下调整：

- 删除知识库管理页面入口
- 删除知识库管理视图文件
- 删除知识库相关路由
- 更新工作台、日志页、登录页、侧边栏文案
- 将后台观察视角改为“文本直答 + 联网搜索 + 会话沉淀”
- 清理 `controlCenter.ts` 中残留的知识文档 mock 结构

### 2.5 用户前端改造

用户文本问答页面已改为真实聊天式界面，支持：

- 会话列表
- 新建会话
- 多轮消息展示
- 问题发送
- 状态提示
- Tavily 来源展示
- 来源链接复制

本次还补齐了两套用户前端包装：

- `apps/mobile-user/pages/qa/index.vue`
- `apps/mobile-user/src/views/QAView.vue`

避免 H5 包和移动端包出现“一个是新逻辑、一个还是旧 mock”的不一致问题。

---

## 3. 关键代码与文件

### 3.1 新增文件

- `backend/app/chat_graph.py`
- `backend/app/chat_store.py`
- `backend/app/routes/chat.py`
- `backend/tests/smoke_test_text_chat.py`
- `apps/mobile-user/services/chat.ts`
- `apps/mobile-user/src/services/chat.ts`

### 3.2 重点修改文件

- `backend/app/config.py`
- `backend/app/model.py`
- `backend/app/schema.py`
- `backend/app/router.py`
- `backend/app/routes/common.py`
- `backend/app/routes/admin.py`
- `backend/requirements.txt`
- `sql/01_schema.sql`
- `apps/mobile-user/pages/qa/index.vue`
- `apps/mobile-user/src/views/QAView.vue`
- `apps/web-admin/src/layouts/WorkspaceLayout.vue`
- `apps/web-admin/src/router/index.ts`
- `apps/web-admin/src/views/admin/AdminDashboardView.vue`
- `apps/web-admin/src/views/admin/AdminLogsView.vue`
- `apps/web-admin/src/data/controlCenter.ts`

### 3.3 删除文件

- `backend/app/rag.py`
- `apps/web-admin/src/views/admin/AdminKnowledgeView.vue`
- `apps/web-admin/src/views/AdminPortal.vue`

---

## 4. 环境与依赖处理

后端依赖已安装到 `conda` 环境 `derma-agent` 中，并已修正 `langgraph` 版本到：

```text
langgraph==1.1.3
```

开发过程中发现该环境之前存在“conda 环境包 + 用户目录包”混装问题。为保证测试稳定性，已执行强制重装到环境内：

```powershell
$env:PYTHONNOUSERSITE='1'
& 'C:\Users\Yeraphael\.conda\envs\derma-agent\python.exe' -m pip install --upgrade --force-reinstall --no-user -r backend/requirements.txt
```

建议后续启动后端时，也优先使用 `derma-agent` 环境内的 `python.exe`，并显式设置：

```powershell
$env:PYTHONNOUSERSITE='1'
```

这样可以避免再次混入用户目录里的旧包。

---

## 5. 测试执行与结果

### 5.1 语法与导入校验

已通过：

- `python -m compileall backend/app backend/tests`
- `from langgraph.graph import START, END, StateGraph`
- `from app.chat_graph import TextChatService`

### 5.2 后端真实冒烟测试

已新增并执行：

```text
backend/tests/smoke_test_text_chat.py
```

执行方式：

```powershell
$env:PYTHONNOUSERSITE='1'
& 'C:\Users\Yeraphael\.conda\envs\derma-agent\python.exe' 'backend/tests/smoke_test_text_chat.py'
```

测试结果：通过

实际通过的用例如下：

| 用例 | 输入 | 预期 | 实际结果 |
|---|---|---|---|
| 普通知识问答 | `湿疹是什么？` | `DIRECT_ANSWER`、不调用工具 | 通过 |
| 多轮追问 | `那它和过敏有什么关系？` | 结合历史理解“它” | 通过 |
| 实时搜索问题 | `最近有没有湿疹治疗的新指南？` | `WEB_SEARCH`、调用 Tavily、返回来源 | 通过 |
| 系统功能问题 | `我怎么上传皮肤图片？` | `SYSTEM_HELP`、不调用工具 | 通过 |
| 医疗风险问题 | `皮肤破溃并且发热怎么办？` | `MEDICAL_RISK`、提醒及时线下就医 | 通过 |
| Tavily 失败兜底 | 模拟 Tavily 异常 | 系统不崩溃、记录错误日志 | 通过 |

本次实际跑出的关键结果：

- `direct_answer` -> `intent=DIRECT_ANSWER`
- `history_followup` -> `intent=DIRECT_ANSWER`
- `web_search` -> `intent=WEB_SEARCH`，`used_tool=true`，`sources=3`
- `system_help` -> `intent=SYSTEM_HELP`
- `medical_risk` -> `intent=MEDICAL_RISK`
- `tavily_fallback` -> 工具异常被正确记录，回答正常降级

### 5.3 前端构建测试

已通过：

```powershell
npm run build:user
npm run build:user:mp-weixin
npm run build:web
```

构建结果说明：

- H5 用户端构建通过
- 微信小程序端构建通过
- 管理员 Web 端构建通过

已额外清理旧 `dist` 产物并重新打包，确认当前产物中不再包含旧 `/rag/qa` 运行路径。

---

## 6. 当前保留说明

### 6.1 本次刻意未做的内容

以下内容按原需求明确不做：

- 多 Agent 协作
- 长期记忆画像
- 自动连续多轮搜索
- 多模型自动路由
- 复杂医学诊断链路

### 6.2 数据库物理清理说明

本次没有自动删除数据库中可能残留的旧 RAG 表，以避免造成不可逆数据丢失。

如果后续你希望进一步做“物理层彻底清表”，建议单独执行一次显式 SQL 迁移，而不是在应用启动阶段自动处理。

### 6.3 构建期警告说明

当前前端构建仍有两类非阻断警告：

- `web-admin` 打包体积较大，Vite 给出 chunk size warning
- `mobile-user` 的 Sass 依赖提示 legacy API / `@import` 未来弃用

这两项不会阻塞本次交付，也不影响当前运行结果。

---

## 7. 最终交付状态

本次改造已达到可交付状态：

- 后端不再走 RAG 知识库
- LangGraph 轻量链路已落地
- 文本问答支持多轮历史
- 支持 Tavily 联网搜索增强
- 支持工具日志保存
- 管理员端知识库入口已删除
- 用户端问答页面已改为真实聊天流
- 后端与前端已完成实际测试和构建验证

如需下一步继续推进，建议优先做这三件事：

1. 增加数据库迁移脚本，正式接管 `chat_sessions / chat_messages / tool_call_logs`；
2. 给管理员端接入真实 `/admin` 统计接口，替换剩余部分 mock 展示数据；
3. 补一组自动化接口测试，纳入后续回归流程。
