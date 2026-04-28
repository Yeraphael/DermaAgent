# 图文智能问诊接入完工报告

## 1. 任务目标

本次工作围绕 `http://127.0.0.1:5174/#/consultation` 完成了从前端 H5 到后端 AI 分析链路的真实接入，不再使用问诊主链路上的 mock 数据。

接入模型为阿里百炼兼容模式视觉模型：

- Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- Model：`qwen3.6-flash`

## 2. 本次已完成内容

### 2.1 前端 H5 问诊主链路改造完成

已打通下面这条真实链路：

1. 用户登录
2. 进入 `#/consultation`
3. 上传真实皮肤图片
4. 提交真实问诊记录
5. 后端触发视觉模型分析
6. 跳转 `#/analysis/:caseId`
7. 展示真实 AI 分析结果
8. 在 `#/history` 中展示真实历史记录与通知

对应改造点：

- 新增真实登录服务：`apps/mobile-user/src/services/auth.ts`
- 新增真实问诊服务：`apps/mobile-user/src/services/consultation.ts`
- 重写基础请求层：`apps/mobile-user/src/services/api.ts`
- 路由守卫改为读取真实登录态：`apps/mobile-user/src/router.ts`

### 2.2 阿里百炼视觉模型接入完成

后端已改为真实调用百炼兼容接口，不再只走本地假数据。

核心实现：

- 文件：`backend/app/ai.py`
- 调用方式：OpenAI 兼容 `/chat/completions`
- 输出格式：结构化 JSON
- 结果字段：
  - `image_observation`
  - `possible_conditions`
  - `risk_level`
  - `care_advice`
  - `hospital_advice`
  - `high_risk_alert`
  - `disclaimer`

### 2.3 本地图片无法公网访问的问题已解决

这是这次接入里最关键的一个点。

原来后端上传后的图片地址是：

`http://127.0.0.1:8000/uploads/...`

外部大模型无法访问本机 `127.0.0.1`，所以现在后端会：

1. 读取本地上传文件
2. 转成 `base64 data URL`
3. 把图片内容直接发给百炼视觉模型

这样本地开发环境也能直接完成真实图像分析。

### 2.4 分析页和历史页已切换到真实接口

已完成：

- `apps/mobile-user/src/views/AnalysisView.vue`
  - 展示真实病例详情
  - 展示真实图片
  - 展示真实 AI 观察、风险等级、护理建议、就医提醒
  - 展示医生回复和通知

- `apps/mobile-user/src/views/HistoryView.vue`
  - 读取真实问诊记录
  - 读取真实通知
  - 组合成统一时间线

### 2.5 页面中文化已统一修复

用户可见页面已统一改成中文，并修掉原先残留的英文和乱码问题，包括：

- 登录页
- 首页
- 智能问诊页
- AI 分析页
- 知识问答页
- 历史记录页
- 健康档案页
- 个人中心页
- 顶部导航与品牌区
- 后端常见错误提示和成功提示

相关文件包括但不限于：

- `apps/mobile-user/src/views/*.vue`
- `apps/mobile-user/src/components/BrandMark.vue`
- `apps/mobile-user/src/shared/portal.ts`
- `backend/app/routes/auth.py`
- `backend/app/routes/common.py`
- `backend/app/routes/consultation.py`

### 2.6 本轮界面可读性与双端体验优化

本轮又补了一次针对“用户端 + 医生/管理端”的可读性优化，重点不是换皮，而是把实际使用时最费眼、最难读、最不利于小程序迁移的部分收干净：

- 用户端 `#/consultation`
  - 上传区从多块大 `+` 占位改成单一主上传入口
  - 明确提示“可多张上传”
  - 上传后的大图与缩略图都尽量完整展示图片全貌，避免被裁切
  - 结构更接近后续小程序可复用的“主预览 + 缩略图切换”模式
- 用户端 `#/analysis/:caseId`
  - “可能相关方向”不再机械重复同一个标题
  - “护理建议”不再每条都只显示“建议”
  - 改成带序号、标签、说明语的结果卡片，更像报告阅读体验
- 用户端全局样式
  - 正文、说明、标签、导航字号整体调大
  - 字色由偏淡调整为更深的蓝灰色，减轻阅读疲劳
- 医生/管理端全局样式
  - 路由标题、副标题修复为正常中文
  - 后台全局字号、字色、卡片密度同步优化
  - Element Plus 的表格、表单、按钮、标签、Tabs 做了统一放大和提亮
- 医生端问诊管理页
  - 问诊图片改成主图预览 + 缩略图切换
  - AI 方向判断改成分层展示，附带优先级和解释语
  - 护理建议改成分条说明卡片，避免重复“建议”字样

## 3. 联调验证结果

### 3.1 前端构建验证

已执行：

```bash
npm run build:user
```

结果：通过。

### 3.2 后端语法验证

已执行：

```bash
python -m compileall backend/app
```

结果：通过。

### 3.3 真实模型冒烟验证

已验证以下能力：

- 登录接口正常
- 图片上传接口正常
- 创建问诊接口正常
- 后端成功调用阿里百炼视觉模型
- 返回模型名为 `qwen3.6-flash`
- AI 结果可正常入库并返回前端

一次成功冒烟的关键信息如下：

- `message`：`问诊提交成功`
- `status`：`AI_DONE`
- `risk_level`：`MEDIUM`
- `model_name`：`qwen3.6-flash`

测试产生的临时问诊数据已清理，不会污染用户历史记录。

## 4. 如何启动

### 4.1 启动 MySQL

当前本地数据库使用的是 phpStudy 自带 MySQL。

可执行文件：

`D:\professionalSofeware\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysqld.exe`

配置文件：

`D:\professionalSofeware\phpstudy_pro\Extensions\MySQL8.0.12\my.ini`

启动命令：

```powershell
D:\professionalSofeware\phpstudy_pro\Extensions\MySQL8.0.12\bin\mysqld.exe --defaults-file=D:\professionalSofeware\phpstudy_pro\Extensions\MySQL8.0.12\my.ini --console
```

### 4.2 启动后端

项目目录：

`F:\GraduationDesign\project\DermaAgent\backend`

启动命令：

```powershell
cd F:\GraduationDesign\project\DermaAgent\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 4.3 启动前端 H5

项目根目录：

`F:\GraduationDesign\project\DermaAgent`

启动命令：

```powershell
cd F:\GraduationDesign\project\DermaAgent
npm run dev:user
```

### 4.4 访问地址

- 前端 H5：`http://127.0.0.1:5174/#/login`
- 问诊页：`http://127.0.0.1:5174/#/consultation`
- 后端接口：`http://127.0.0.1:8000/api/v1`

### 4.5 演示账号

- 用户名：`user01`
- 密码：`12345678`

## 5. 目录结构说明

### 5.1 前端用户端

目录：

`apps/mobile-user/src`

关键结构：

- `views/`
  - 页面视图
  - 本次重点改动：`LoginView.vue`、`ConsultationView.vue`、`AnalysisView.vue`、`HistoryView.vue`
- `services/`
  - 前端接口调用层
  - 本次新增：`auth.ts`、`consultation.ts`
  - 本次重写：`api.ts`
- `shared/portal.ts`
  - 首页、知识问答、档案页用到的本地展示数据和工具函数
- `components/`
  - 通用组件，如品牌区、风险标签、方向条

### 5.2 后端服务

目录：

`backend/app`

关键结构：

- `routes/auth.py`
  - 登录、注册、改密
- `routes/common.py`
  - 图片上传、RAG 问答等公共接口
- `routes/consultation.py`
  - 问诊创建、详情、消息、AI 分析相关接口
- `ai.py`
  - 百炼视觉模型接入核心
  - 包含本地图片转 `base64 data URL` 的逻辑
- `service.py`
  - 问诊详情组装、AI 分析入库、通知创建等业务逻辑
- `model.py`
  - 数据库 ORM 模型定义

### 5.3 文档

目录：

`docs`

当前已有：

- `docs/consultation-real-vlm-plan.md`
  - 真实视觉模型接入方案
- `docs/consultation-completion-report.md`
  - 本完工报告

## 6. 当前配置说明

本地 `.env` 已按真实模型方式配置：

- `AI_MODE=real`
- `QWEN_BASE_URL` 已指向百炼兼容模式
- `QWEN_VISUAL_MODEL=qwen3.6-flash`
- `QWEN_TEXT_MODEL=qwen3.6-flash`

注意：

- `API Key` 只保留在本地 `.env`
- 不建议提交到仓库

## 7. 已知说明

### 7.1 首页 / 知识问答 / 档案页

这些页面当前已经全部改成中文，但其中部分内容仍属于前端本地展示数据，不影响真实问诊主链路。

### 7.2 真实视觉分析结果依赖图片质量

如果上传的不是实际皮肤图片，模型仍然会返回结构化结果，但观察内容可能偏保守或提示信息不足。这属于模型输入质量问题，不是接口问题。

## 8. 结论

本次已经完成你要求的“真实图文智能问诊模块”主链路落地：

- 前端不再只做 demo
- 后端已接真实视觉模型
- 图片本地开发可直连模型分析
- 分析页和历史页可展示真实结果
- 所有用户端页面已统一中文化
