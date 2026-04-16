# 肤联智诊

基于 AI 的皮肤病智慧诊断小助手，包含完整可运行的前端、后端、SQL 初始化脚本与本地部署说明。

## 工程组成

- `apps/mobile-user`：uni-app + Vue 3 + TypeScript 用户端
- `apps/web-admin`：Vue 3 + Vite + TypeScript + Pinia + Vue Router + Axios + Element Plus 医生 / 管理员端
- `backend`：FastAPI + SQLAlchemy + JWT + RBAC 后端
- `sql`：MySQL 建库、建表、初始化与统计脚本
- `deploy/nginx`：本地 Nginx 反向代理示例
- `docs`：UI Design Token 与说明文档

## 版本选型

- Python：3.13
- FastAPI：0.115.12
- SQLAlchemy：2.0.39
- pydantic：2.11.3
- pydantic-settings：2.10.1
- Vue：3.4.28
- Vite：5.2.8
- Element Plus：2.8.8
- uni-app：`@dcloudio/uni-app@3.0.0-5000720260410001`
- uni Vite 插件：`@dcloudio/vite-plugin-uni@3.0.0-5000720260410001`

## 重要说明

- MySQL 是主业务真实数据源
- Qdrant 本次默认 `mock`
- 千问模型本次默认 `mock`
- 千问 API Key 与 Base URL 只能从环境变量读取

## 环境建议

- 强烈建议为本项目单独创建 Conda 环境
- 不要直接复用已经安装过 `docling`、`langchain-community`、`transformers`、`qdrant-client` 等包的旧环境
- 如果复用旧环境，`pip` 可能会报很多“其它包缺少依赖”或“版本冲突”提示；这通常是旧环境被别的项目污染，不是本项目核心依赖本身损坏

## 默认测试账号

- 用户：`user01 / 12345678`
- 医生：`doctor01 / 12345678`
- 管理员：`admin01 / 12345678`

## 本地地址

- 后端：`http://127.0.0.1:8000`
- 后端 API：`http://127.0.0.1:8000/api/v1`
- Web 管理端：`http://127.0.0.1:5173`
- uni-app H5 用户端：`http://127.0.0.1:5174`

## 启动顺序

1. 创建独立 Conda 环境
2. 配置 `.env`
3. 执行 SQL 初始化
4. 启动 FastAPI
5. 启动 Web 管理端
6. 启动 uni-app 用户端

详细步骤见 [项目启动与部署说明.md](./项目启动与部署说明.md)。
