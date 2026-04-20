# 肤联智诊 DermaAgent

面向答辩展示与产品化演示的 AI 皮肤健康辅助系统，包含：

- 用户端 Web/H5
- 用户端小程序风格页面
- 医生端工作台
- 管理员端中台
- FastAPI 后端与 MySQL 数据层

## 项目结构

- `apps/mobile-user`
  用户端前端，基于 `uni-app + Vue 3 + TypeScript`，同时覆盖 H5 与微信小程序构建。
- `apps/web-admin`
  医生端与管理员端，基于 `Vue 3 + Vite + TypeScript + Pinia + Vue Router`。
- `backend`
  FastAPI 后端，包含认证、问诊、医生、管理、RAG 问答等接口。
- `sql`
  数据库建库建表与初始化脚本。
- `docs`
  设计规范与补充文档。

## 当前版本亮点

- 用户端重构为高保真 AI 医疗科技风，支持首页、问诊提交、AI 结果、知识问答、历史记录、健康档案。
- 小程序风格页面与 H5 视觉语言统一，适合演示与迁移。
- 医生端重构为工作台、三栏问诊详情、患者管理。
- 管理员端重构为数据看板、用户管理、医生管理、知识库流程、系统配置、日志统计、公告管理。
- 根目录保留了 5 张设计稿 PNG 作为本次还原参考。

## 技术栈

- 前端
  - Vue 3
  - Vite
  - TypeScript
  - Pinia
  - Vue Router
  - Element Plus
  - uni-app
- 后端
  - FastAPI
  - SQLAlchemy
  - MySQL
  - JWT

## 环境要求

- Node.js 18+
- npm 9+
- Python 3.11+ 或兼容版本
- MySQL 8+

## 安装依赖

根目录执行：

```bash
npm install
```

后端依赖请参考：

- [项目启动与部署说明.md](/F:/GraduationDesign/project/DermaAgent/项目启动与部署说明.md)
- [微信小程序问题排查与打包说明.md](/F:/GraduationDesign/project/DermaAgent/微信小程序问题排查与打包说明.md)

## 前端启动

用户端 H5：

```bash
npm run dev:user
```

医生端 / 管理员端：

```bash
npm run dev:web
```

微信小程序开发构建：

```bash
npm run dev:user:mp-weixin
```

## 前端构建

医生端 / 管理员端：

```bash
npm run build:web
```

用户端 H5：

```bash
npm run build:user
```

微信小程序：

```bash
npm run build:user:mp-weixin
```

微信开发者工具导入目录：

```text
dist/build/mp-weixin
```

## 默认访问地址

- 后端 API：`http://127.0.0.1:8000/api/v1`
- 医生端 / 管理员端：`http://127.0.0.1:5173`
- 用户端 H5：`http://127.0.0.1:5174`

## 演示账号

- 用户端：`user01 / 12345678`
- 医生端：`doctor01 / 12345678`
- 管理端：`admin01 / 12345678`

## 后端说明

- 默认接口前缀：`/api/v1`
- 当前仓库包含后端完整实现与接口文档
- 接口基准文档：`肤联智诊_接口文档.md`

启动后端前请先完成：

1. 配置根目录 `.env`
2. 初始化 MySQL 数据库
3. 按文档启动 FastAPI 服务

## 文档索引

- [肤联智诊_接口文档.md](/F:/GraduationDesign/project/DermaAgent/肤联智诊_接口文档.md)
- [肤联智诊_系统分析文档.md](/F:/GraduationDesign/project/DermaAgent/肤联智诊_系统分析文档.md)
- [肤联智诊_系统设计文档.md](/F:/GraduationDesign/project/DermaAgent/肤联智诊_系统设计文档.md)
- [项目启动与部署说明.md](/F:/GraduationDesign/project/DermaAgent/项目启动与部署说明.md)
- [微信小程序问题排查与打包说明.md](/F:/GraduationDesign/project/DermaAgent/微信小程序问题排查与打包说明.md)

## 已验证命令

本次提交前已验证：

- `npm run build:web`
- `npm run build:user`
- `npm run build:user:mp-weixin`

已知提示：

- `web-admin` 构建有 chunk size 警告，但不影响产物生成。
- `uni-app` 构建有 Sass 旧 API / `@import` deprecation 警告，不影响当前运行。
