# 肤联智诊数据库数据字典

> 说明  
> 本文仅统计当前正式实现使用的 `19` 张核心表，来源为 `sql/01_schema.sql` 与 `backend/app/model.py`。  
> 字段类型以当前建表脚本为准。  
> “主键/外键”列采用以下写法：
> - `PK`：主键
> - `FK -> xxx.id`：外键
> - `PK, FK -> xxx.id`：既是主键又是外键
> - `-`：普通字段

## 1. `users`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `users` | `PK` | `id` | `BIGINT` | 用户账号主键 |
| `users` | `-` | `username` | `VARCHAR(50)` | 登录用户名，用户端通常与手机号一致 |
| `users` | `-` | `password_hash` | `VARCHAR(255)` | 密码哈希值 |
| `users` | `-` | `role_type` | `VARCHAR(20)` | 角色类型，`USER/DOCTOR/ADMIN` |
| `users` | `-` | `phone` | `VARCHAR(20)` | 手机号 |
| `users` | `-` | `email` | `VARCHAR(100)` | 邮箱 |
| `users` | `-` | `avatar_url` | `VARCHAR(500)` | 头像地址 |
| `users` | `-` | `status` | `INT` | 账号状态，`1` 启用，`0` 停用 |
| `users` | `-` | `last_login_at` | `DATETIME` | 最近登录时间 |
| `users` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `users` | `-` | `updated_at` | `DATETIME` | 更新时间 |
| `users` | `-` | `is_deleted` | `INT` | 软删除标记 |

## 2. `user_profiles`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `user_profiles` | `PK` | `id` | `BIGINT` | 用户基础档案主键 |
| `user_profiles` | `FK -> users.id` | `user_id` | `BIGINT` | 关联账号，一对一 |
| `user_profiles` | `-` | `real_name` | `VARCHAR(50)` | 真实姓名 |
| `user_profiles` | `-` | `gender` | `VARCHAR(10)` | 性别 |
| `user_profiles` | `-` | `age` | `INT` | 年龄 |
| `user_profiles` | `-` | `birthday` | `DATE` | 出生日期 |
| `user_profiles` | `-` | `city` | `VARCHAR(50)` | 城市 |
| `user_profiles` | `-` | `occupation` | `VARCHAR(50)` | 职业 |
| `user_profiles` | `-` | `emergency_contact` | `VARCHAR(50)` | 紧急联系人 |
| `user_profiles` | `-` | `emergency_phone` | `VARCHAR(20)` | 紧急联系电话 |
| `user_profiles` | `-` | `remark` | `VARCHAR(255)` | 备注 |
| `user_profiles` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `user_profiles` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 3. `health_profiles`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `health_profiles` | `PK` | `id` | `BIGINT` | 健康档案主键 |
| `health_profiles` | `FK -> user_profiles.id` | `user_profile_id` | `BIGINT` | 关联基础档案，一对一 |
| `health_profiles` | `-` | `allergy_history` | `TEXT` | 过敏史 |
| `health_profiles` | `-` | `past_medical_history` | `TEXT` | 既往病史 |
| `health_profiles` | `-` | `medication_history` | `TEXT` | 用药史 |
| `health_profiles` | `-` | `skin_type` | `VARCHAR(50)` | 肤质类型 |
| `health_profiles` | `-` | `skin_sensitivity` | `VARCHAR(50)` | 敏感程度 |
| `health_profiles` | `-` | `sleep_pattern` | `VARCHAR(50)` | 睡眠习惯 |
| `health_profiles` | `-` | `diet_preference` | `VARCHAR(80)` | 饮食偏好 |
| `health_profiles` | `-` | `special_notes` | `TEXT` | 特殊说明 |
| `health_profiles` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 4. `doctors`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `doctors` | `PK` | `id` | `BIGINT` | 医生业务主键 |
| `doctors` | `FK -> users.id` | `user_id` | `BIGINT` | 关联医生账号 |
| `doctors` | `-` | `doctor_name` | `VARCHAR(50)` | 医生姓名 |
| `doctors` | `-` | `department` | `VARCHAR(50)` | 所属科室 |
| `doctors` | `-` | `title_name` | `VARCHAR(50)` | 医生职称 |
| `doctors` | `-` | `hospital_name` | `VARCHAR(100)` | 所属医院 |
| `doctors` | `-` | `specialty` | `VARCHAR(255)` | 擅长方向 |
| `doctors` | `-` | `intro` | `TEXT` | 医生简介 |
| `doctors` | `-` | `license_no` | `VARCHAR(100)` | 执业证号 |
| `doctors` | `-` | `audit_status` | `VARCHAR(20)` | 审核状态 |
| `doctors` | `-` | `audit_remark` | `VARCHAR(255)` | 审核备注 |
| `doctors` | `-` | `service_status` | `INT` | 服务状态，`1` 服务中，`0` 暂停 |
| `doctors` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `doctors` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 5. `admins`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `admins` | `PK` | `id` | `BIGINT` | 管理员业务主键 |
| `admins` | `FK -> users.id` | `user_id` | `BIGINT` | 关联管理员账号 |
| `admins` | `-` | `admin_name` | `VARCHAR(50)` | 管理员姓名 |
| `admins` | `-` | `job_title` | `VARCHAR(50)` | 岗位名称 |
| `admins` | `-` | `permissions_summary` | `VARCHAR(255)` | 权限摘要 |
| `admins` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `admins` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 6. `consultations`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `consultations` | `PK` | `id` | `BIGINT` | 问诊主键 |
| `consultations` | `-` | `case_no` | `VARCHAR(50)` | 问诊单号 |
| `consultations` | `FK -> users.id` | `user_id` | `BIGINT` | 发起问诊的用户 |
| `consultations` | `FK -> doctors.id` | `assigned_doctor_id` | `BIGINT` | 分配的医生 |
| `consultations` | `-` | `summary_title` | `VARCHAR(120)` | 摘要标题 |
| `consultations` | `-` | `chief_complaint` | `TEXT` | 主诉内容 |
| `consultations` | `-` | `onset_duration` | `VARCHAR(50)` | 发病时长 |
| `consultations` | `-` | `itch_level` | `INT` | 瘙痒等级 |
| `consultations` | `-` | `pain_level` | `INT` | 疼痛等级 |
| `consultations` | `-` | `spread_flag` | `INT` | 是否扩散 |
| `consultations` | `-` | `status` | `VARCHAR(30)` | 问诊状态 |
| `consultations` | `-` | `risk_level` | `VARCHAR(20)` | 风险等级 |
| `consultations` | `-` | `ai_enabled` | `INT` | 是否启用 AI 分析 |
| `consultations` | `-` | `need_doctor_review` | `INT` | 是否需要医生复核 |
| `consultations` | `-` | `ai_confidence` | `FLOAT` | AI 置信度估计 |
| `consultations` | `-` | `abnormal_flag` | `INT` | 是否异常标记 |
| `consultations` | `-` | `abnormal_note` | `TEXT` | 异常说明 |
| `consultations` | `-` | `archived_flag` | `INT` | 是否归档 |
| `consultations` | `-` | `archived_at` | `DATETIME` | 归档时间 |
| `consultations` | `-` | `submitted_at` | `DATETIME` | 提交时间 |
| `consultations` | `-` | `closed_at` | `DATETIME` | 关闭时间 |
| `consultations` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `consultations` | `-` | `updated_at` | `DATETIME` | 更新时间 |
| `consultations` | `-` | `is_deleted` | `INT` | 软删除标记 |

## 7. `consultation_images`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `consultation_images` | `PK` | `id` | `BIGINT` | 问诊图片主键 |
| `consultation_images` | `FK -> consultations.id` | `consultation_id` | `BIGINT` | 所属问诊单 |
| `consultation_images` | `-` | `file_name` | `VARCHAR(255)` | 文件名 |
| `consultation_images` | `-` | `file_url` | `VARCHAR(2048)` | 图片访问地址 |
| `consultation_images` | `-` | `file_size` | `BIGINT` | 文件大小 |
| `consultation_images` | `-` | `file_type` | `VARCHAR(50)` | 文件类型 |
| `consultation_images` | `-` | `sort_no` | `INT` | 图片排序号 |
| `consultation_images` | `-` | `uploaded_at` | `DATETIME` | 上传时间 |

## 8. `ai_analysis_records`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `ai_analysis_records` | `PK` | `id` | `BIGINT` | AI 分析记录主键 |
| `ai_analysis_records` | `FK -> consultations.id` | `consultation_id` | `BIGINT` | 所属问诊单 |
| `ai_analysis_records` | `-` | `model_name` | `VARCHAR(100)` | 使用的模型名称 |
| `ai_analysis_records` | `-` | `prompt_version` | `VARCHAR(50)` | 提示词版本 |
| `ai_analysis_records` | `-` | `input_summary` | `TEXT` | 输入摘要 |
| `ai_analysis_records` | `-` | `image_observation` | `TEXT` | 图像观察结果 |
| `ai_analysis_records` | `-` | `possible_conditions` | `TEXT` | 可能病情方向 |
| `ai_analysis_records` | `-` | `risk_level` | `VARCHAR(20)` | 风险等级 |
| `ai_analysis_records` | `-` | `care_advice` | `TEXT` | 护理建议 |
| `ai_analysis_records` | `-` | `hospital_advice` | `TEXT` | 医院/线下就医建议 |
| `ai_analysis_records` | `-` | `high_risk_alert` | `TEXT` | 高风险提醒 |
| `ai_analysis_records` | `-` | `disclaimer` | `VARCHAR(255)` | 医疗免责声明 |
| `ai_analysis_records` | `-` | `raw_response` | `TEXT` | 原始模型返回内容 |
| `ai_analysis_records` | `-` | `analysis_status` | `VARCHAR(20)` | 分析状态 |
| `ai_analysis_records` | `-` | `fail_reason` | `VARCHAR(255)` | 失败或回退原因 |
| `ai_analysis_records` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 9. `consultation_messages`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `consultation_messages` | `PK` | `id` | `BIGINT` | 问诊沟通消息主键 |
| `consultation_messages` | `FK -> consultations.id` | `consultation_id` | `BIGINT` | 所属问诊单 |
| `consultation_messages` | `-` | `sender_role` | `VARCHAR(20)` | 发送者角色 |
| `consultation_messages` | `-` | `sender_id` | `BIGINT` | 发送者账号 ID |
| `consultation_messages` | `-` | `message_type` | `VARCHAR(20)` | 消息类型 |
| `consultation_messages` | `-` | `content` | `TEXT` | 消息内容 |
| `consultation_messages` | `-` | `created_at` | `DATETIME` | 发送时间 |

## 10. `consultation_replies`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `consultation_replies` | `PK` | `id` | `BIGINT` | 医生回复主键 |
| `consultation_replies` | `FK -> consultations.id` | `consultation_id` | `BIGINT` | 所属问诊单 |
| `consultation_replies` | `FK -> doctors.id` | `doctor_id` | `BIGINT` | 回复医生 |
| `consultation_replies` | `-` | `content` | `TEXT` | 医生回复整合内容 |
| `consultation_replies` | `-` | `first_impression` | `TEXT` | 初步判断 |
| `consultation_replies` | `-` | `care_advice` | `TEXT` | 护理建议 |
| `consultation_replies` | `-` | `suggest_offline_visit` | `INT` | 是否建议线下就医 |
| `consultation_replies` | `-` | `suggest_follow_up` | `INT` | 是否建议复查 |
| `consultation_replies` | `-` | `doctor_remark` | `TEXT` | 医生备注 |
| `consultation_replies` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `consultation_replies` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 11. `chat_sessions`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `chat_sessions` | `PK` | `id` | `BIGINT` | 文本问答会话主键 |
| `chat_sessions` | `FK -> users.id` | `user_id` | `BIGINT` | 所属用户 |
| `chat_sessions` | `-` | `title` | `VARCHAR(120)` | 会话标题 |
| `chat_sessions` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `chat_sessions` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 12. `chat_messages`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `chat_messages` | `PK` | `id` | `BIGINT` | 文本问答消息主键 |
| `chat_messages` | `FK -> chat_sessions.id` | `session_id` | `BIGINT` | 所属会话 |
| `chat_messages` | `FK -> users.id` | `user_id` | `BIGINT` | 所属用户 |
| `chat_messages` | `-` | `role` | `VARCHAR(20)` | 消息角色，用户或助手 |
| `chat_messages` | `-` | `content` | `TEXT` | 消息内容 |
| `chat_messages` | `-` | `intent` | `VARCHAR(30)` | 路由后的意图类型 |
| `chat_messages` | `-` | `used_tool` | `INT` | 是否调用工具 |
| `chat_messages` | `-` | `tool_name` | `VARCHAR(50)` | 调用工具名称 |
| `chat_messages` | `-` | `sources_json` | `TEXT` | 搜索来源或引用来源 JSON |
| `chat_messages` | `-` | `model_name` | `VARCHAR(100)` | 使用的文本模型 |
| `chat_messages` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 13. `tool_call_logs`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `tool_call_logs` | `PK` | `id` | `BIGINT` | 工具调用日志主键 |
| `tool_call_logs` | `FK -> chat_sessions.id` | `session_id` | `BIGINT` | 所属会话 |
| `tool_call_logs` | `FK -> chat_messages.id` | `message_id` | `BIGINT` | 关联助手消息 |
| `tool_call_logs` | `-` | `tool_name` | `VARCHAR(50)` | 工具名称 |
| `tool_call_logs` | `-` | `query` | `TEXT` | 调用请求内容 |
| `tool_call_logs` | `-` | `result_json` | `TEXT` | 工具返回结果 JSON |
| `tool_call_logs` | `-` | `latency_ms` | `INT` | 调用耗时毫秒数 |
| `tool_call_logs` | `-` | `success` | `INT` | 是否成功 |
| `tool_call_logs` | `-` | `error_message` | `TEXT` | 错误信息 |
| `tool_call_logs` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 14. `system_configs`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `system_configs` | `PK` | `id` | `BIGINT` | 系统配置主键 |
| `system_configs` | `-` | `config_key` | `VARCHAR(100)` | 配置键名 |
| `system_configs` | `-` | `config_value` | `TEXT` | 配置值 |
| `system_configs` | `-` | `config_group` | `VARCHAR(50)` | 配置分组 |
| `system_configs` | `-` | `description` | `VARCHAR(255)` | 配置说明 |
| `system_configs` | `FK -> users.id` | `updated_by` | `BIGINT` | 最近更新人 |
| `system_configs` | `-` | `updated_at` | `DATETIME` | 最近更新时间 |

## 15. `announcements`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `announcements` | `PK` | `id` | `BIGINT` | 公告主键 |
| `announcements` | `-` | `title` | `VARCHAR(200)` | 公告标题 |
| `announcements` | `-` | `content` | `TEXT` | 公告正文 |
| `announcements` | `-` | `status` | `INT` | 公告状态 |
| `announcements` | `-` | `publish_scope` | `VARCHAR(50)` | 发布范围 |
| `announcements` | `FK -> users.id` | `published_by` | `BIGINT` | 发布人 |
| `announcements` | `-` | `published_at` | `DATETIME` | 发布时间 |
| `announcements` | `-` | `created_at` | `DATETIME` | 创建时间 |
| `announcements` | `-` | `updated_at` | `DATETIME` | 更新时间 |

## 16. `notifications`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `notifications` | `PK` | `id` | `BIGINT` | 通知主键 |
| `notifications` | `FK -> users.id` | `user_id` | `BIGINT` | 接收通知的用户 |
| `notifications` | `-` | `title` | `VARCHAR(120)` | 通知标题 |
| `notifications` | `-` | `content` | `TEXT` | 通知内容 |
| `notifications` | `-` | `notification_type` | `VARCHAR(30)` | 通知类型 |
| `notifications` | `-` | `related_business_type` | `VARCHAR(30)` | 关联业务类型 |
| `notifications` | `-` | `related_business_id` | `BIGINT` | 关联业务主键 |
| `notifications` | `-` | `read_flag` | `INT` | 是否已读 |
| `notifications` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 17. `doctor_ai_feedbacks`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `doctor_ai_feedbacks` | `PK` | `id` | `BIGINT` | 医生 AI 反馈主键 |
| `doctor_ai_feedbacks` | `FK -> consultations.id` | `consultation_id` | `BIGINT` | 所属问诊单 |
| `doctor_ai_feedbacks` | `FK -> doctors.id` | `doctor_id` | `BIGINT` | 反馈医生 |
| `doctor_ai_feedbacks` | `-` | `ai_accuracy` | `VARCHAR(20)` | AI 准确度评价 |
| `doctor_ai_feedbacks` | `-` | `correction_note` | `TEXT` | 修正意见 |
| `doctor_ai_feedbacks` | `-` | `knowledge_gap_note` | `TEXT` | 知识缺口说明 |
| `doctor_ai_feedbacks` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 18. `operation_logs`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `operation_logs` | `PK` | `id` | `BIGINT` | 操作日志主键 |
| `operation_logs` | `FK -> users.id` | `account_id` | `BIGINT` | 操作账号 |
| `operation_logs` | `-` | `role_type` | `VARCHAR(20)` | 操作角色类型 |
| `operation_logs` | `-` | `module_name` | `VARCHAR(50)` | 操作模块 |
| `operation_logs` | `-` | `operation_type` | `VARCHAR(50)` | 操作类型 |
| `operation_logs` | `-` | `business_id` | `VARCHAR(100)` | 关联业务标识 |
| `operation_logs` | `-` | `operation_desc` | `VARCHAR(255)` | 操作描述 |
| `operation_logs` | `-` | `request_ip` | `VARCHAR(50)` | 请求 IP |
| `operation_logs` | `-` | `operation_result` | `VARCHAR(20)` | 操作结果 |
| `operation_logs` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 19. `statistics_snapshots`

| 数据名称 | 主键/外键 | 字段名称 | 类型 | 注释 |
| --- | --- | --- | --- | --- |
| `statistics_snapshots` | `PK` | `id` | `BIGINT` | 统计快照主键 |
| `statistics_snapshots` | `-` | `snapshot_date` | `DATE` | 快照日期 |
| `statistics_snapshots` | `-` | `metric_key` | `VARCHAR(50)` | 指标键名 |
| `statistics_snapshots` | `-` | `metric_value` | `FLOAT` | 指标值 |
| `statistics_snapshots` | `-` | `metric_group` | `VARCHAR(30)` | 指标分组 |
| `statistics_snapshots` | `-` | `created_at` | `DATETIME` | 创建时间 |

## 20. 遗留/可选旧表

以下表出现在 `sql/03_seed_business.sql` 中，但不属于当前正式实现主库：

| 数据名称 | 当前状态 | 说明 |
| --- | --- | --- |
| `knowledge_documents` | 遗留/可选 | 旧知识文档主表 |
| `knowledge_chunks_metadata` | 遗留/可选 | 旧知识分片表 |
| `qa_records` | 遗留/可选 | 旧问答记录表 |

