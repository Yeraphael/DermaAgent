# 肤联智诊 DermaAgent

面向真实业务流程设计的皮肤健康智能问诊系统，包含用户端、医生端、管理员端与 FastAPI 后端。

当前版本已经完成医生端与管理员端的产品化重构，并打通了用户提交问诊、AI 分析、医生处理、管理员监管的核心闭环。

## 当前交付范围

- 用户端：图文问诊、AI 分析结果查看、历史记录、健康档案、消息提醒
- 医生端：工作台、问诊管理、患者档案、医生回复、AI 结果反馈
- 管理端：控制台、用户管理、医生管理、咨询记录、系统配置、日志监控
- 后端：认证鉴权、角色隔离、问诊流转、配置持久化、操作留痕、AI 分析服务
- 数据库：核心业务表、产品化字段补齐、增量迁移脚本、基础种子数据

## 项目结构

- `apps/mobile-user`
  用户端前端，基于 `uni-app + Vue 3 + TypeScript`，支持 H5 与微信小程序构建。
- `apps/web-admin`
  医生端与管理员端前端，基于 `Vue 3 + Vite + TypeScript + Pinia + Vue Router + Element Plus`。
- `backend`
  FastAPI 后端，包含认证、用户、问诊、医生、管理员、AI 服务与公共接口。
- `sql`
  数据库建表、种子数据与增量迁移脚本。
- `docs`
  医生端与管理员端设计参考图，以及补充文档。
- `PROJECT_COMPLETION_REPORT.md`
  本轮产品化重构的完整完工报告。

## 业务模块

### 医生端

- 工作台
- 问诊管理
- 患者档案

### 管理端

- 控制台
- 用户管理
- 医生管理
- 咨询记录
- 系统配置
- 日志监控

## 技术栈

### 前端

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus
- uni-app

### 后端

- FastAPI
- SQLAlchemy
- MySQL
- JWT
- httpx

## 环境要求

- Node.js 18+
- npm 9+
- Python 3.11+
- MySQL 8+

## 快速开始

### 1. 安装前端依赖

在仓库根目录执行：

```bash
npm install
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

根目录提供了 `.env.example`，可复制为 `.env` 后按实际环境修改：

```env
BASE_URL=http://127.0.0.1:8000
API_PREFIX=/api/v1
JWT_SECRET=replace-with-a-long-random-secret

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=derma_agent

AI_MODE=mock
QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_VISUAL_MODEL=qwen3.6-flash
QWEN_TEXT_MODEL=qwen3.6-flash

VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

说明：

- `AI_MODE=mock` 表示默认使用本地分析兜底逻辑，适合本地联调和验收。
- 若需接入真实模型，请配置 `QWEN_API_KEY` 并将 `AI_MODE=real`。

### 4. 初始化数据库

首次建库推荐执行：

```bash
mysql -u root -p < sql/01_schema.sql
mysql -u root -p < sql/02_seed_base.sql
mysql -u root -p < sql/04_seed_stats.sql
```

说明：

- `sql/01_schema.sql`：完整建表
- `sql/02_seed_base.sql`：基础账号、患者档案、医生、管理员、系统配置等核心数据
- `sql/04_seed_stats.sql`：控制台和日志页使用的统计与样例日志数据
- `sql/03_seed_business.sql`：旧知识问答扩展数据，仅在保留对应旧表结构时按需执行

若是对已有库做增量升级，请执行：

```bash
mysql -u root -p < sql/migrations/20260429_doctor_admin_productization.sql
```

### 5. 启动后端

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. 启动前端

医生端 / 管理端：

```bash
npm run dev:web
```

用户端 H5：

```bash
npm run dev:user
```

用户端微信小程序：

```bash
npm run dev:user:mp-weixin
```

## 构建命令

- 医生端 / 管理端：`npm run build:web`
- 用户端 H5：`npm run build:user`
- 用户端微信小程序：`npm run build:user:mp-weixin`

## 默认访问地址

- 后端 API：`http://127.0.0.1:8000/api/v1`
- 医生端 / 管理端：`http://127.0.0.1:5173`
- 用户端 H5：`http://127.0.0.1:5174`

## 已验证账号

当前种子数据中已验证可用：

- 普通用户：`18753701377 / 12345678`
- 医生：`doctor01 / 12345678`
- 管理员：`admin01 / 12345678`

## 文档索引

- [PROJECT_COMPLETION_REPORT.md](./PROJECT_COMPLETION_REPORT.md)
- [项目启动与部署说明.md](./项目启动与部署说明.md)
- [肤联智诊_接口文档.md](./肤联智诊_接口文档.md)
- [肤联智诊_系统分析文档.md](./肤联智诊_系统分析文档.md)
- [肤联智诊_系统设计文档.md](./肤联智诊_系统设计文档.md)
- [微信小程序问题排查与打包说明.md](./微信小程序问题排查与打包说明.md)

## 当前验证结果

本轮已完成并验证：

- `npm run build:web`
- `npm run build:user`
- 后端闭环冒烟验证
  - 用户提交图文问诊
  - 系统分配医生
  - 医生查看并回复问诊
  - 医生提交 AI 结果反馈
  - 用户端查看医生回复
  - 管理端查看全平台咨询与反馈

## 上线说明

当前版本已经满足本地部署、联调演示和阶段性交付验收。

如果需要直接面向真实公网用户正式上线，建议至少再完成以下生产准备：

- 替换 `.env` 中的默认密钥与数据库密码
- 关闭默认种子账号或重置正式密码
- 配置 HTTPS、Nginx、备份与监控告警
- 将 AI 服务切换到正式模型配置
- 完成对象存储、图片安全策略与日志保留策略
- 做一轮安全测试、压力测试和异常恢复验证
