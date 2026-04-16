from __future__ import annotations

import hashlib
import json
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_NAME = "derma_agent"
PASSWORD = "12345678"


def sql_value(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(value, date):
        return f"'{value.isoformat()}'"
    text = str(value).replace("\\", "\\\\").replace("'", "''").replace("\n", "\\n")
    return f"'{text}'"


def build_insert(table: str, columns: list[str], rows: list[dict]) -> str:
    head = f"INSERT INTO `{table}` ({', '.join(f'`{column}`' for column in columns)}) VALUES\n"
    values = []
    for row in rows:
        values.append("(" + ", ".join(sql_value(row.get(column)) for column in columns) + ")")
    return head + ",\n".join(values) + ";\n"


def hash_password(username: str) -> str:
    salt = hashlib.sha256(f"derma-agent-{username}".encode("utf-8")).hexdigest()[:32]
    digest = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode("utf-8"), salt.encode("utf-8"), 180000).hex()
    return f"{salt}${digest}"


def svg_data_uri(label: str, hue_a: str, hue_b: str) -> str:
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="420" height="320" viewBox="0 0 420 320">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{hue_a}" />
      <stop offset="100%" stop-color="{hue_b}" />
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="420" height="320" rx="40" fill="url(#g)" />
  <circle cx="318" cy="84" r="64" fill="rgba(255,255,255,0.14)" />
  <circle cx="120" cy="242" r="96" fill="rgba(255,255,255,0.10)" />
  <rect x="42" y="58" width="180" height="180" rx="56" fill="rgba(255,255,255,0.18)" />
  <text x="44" y="42" fill="#FFFFFF" font-size="22" font-family="Arial">DermaAgent</text>
  <text x="72" y="162" fill="#FFFFFF" font-size="44" font-family="Arial">IMG</text>
  <text x="70" y="286" fill="#E8FFF8" font-size="24" font-family="Arial">{label}</text>
</svg>
""".strip()
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


def build_schema() -> str:
    return """SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS `derma_agent` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `derma_agent`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `statistics_snapshots`;
DROP TABLE IF EXISTS `operation_logs`;
DROP TABLE IF EXISTS `doctor_ai_feedbacks`;
DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `announcements`;
DROP TABLE IF EXISTS `system_configs`;
DROP TABLE IF EXISTS `knowledge_chunks_metadata`;
DROP TABLE IF EXISTS `knowledge_documents`;
DROP TABLE IF EXISTS `qa_records`;
DROP TABLE IF EXISTS `consultation_replies`;
DROP TABLE IF EXISTS `consultation_messages`;
DROP TABLE IF EXISTS `ai_analysis_records`;
DROP TABLE IF EXISTS `consultation_images`;
DROP TABLE IF EXISTS `consultations`;
DROP TABLE IF EXISTS `admins`;
DROP TABLE IF EXISTS `doctors`;
DROP TABLE IF EXISTS `health_profiles`;
DROP TABLE IF EXISTS `user_profiles`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `users` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role_type` VARCHAR(20) NOT NULL,
  `phone` VARCHAR(20) NULL,
  `email` VARCHAR(100) NULL,
  `avatar_url` VARCHAR(500) NULL,
  `status` INT NOT NULL DEFAULT 1,
  `last_login_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `is_deleted` INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user_profiles` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL UNIQUE,
  `real_name` VARCHAR(50) NULL,
  `gender` VARCHAR(10) NULL,
  `age` INT NULL,
  `birthday` DATE NULL,
  `city` VARCHAR(50) NULL,
  `occupation` VARCHAR(50) NULL,
  `emergency_contact` VARCHAR(50) NULL,
  `emergency_phone` VARCHAR(20) NULL,
  `remark` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_user_profiles_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `health_profiles` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_profile_id` BIGINT NOT NULL UNIQUE,
  `allergy_history` TEXT NULL,
  `past_medical_history` TEXT NULL,
  `medication_history` TEXT NULL,
  `skin_type` VARCHAR(50) NULL,
  `skin_sensitivity` VARCHAR(50) NULL,
  `sleep_pattern` VARCHAR(50) NULL,
  `diet_preference` VARCHAR(80) NULL,
  `special_notes` TEXT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_health_profiles_user_profile_id` FOREIGN KEY (`user_profile_id`) REFERENCES `user_profiles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `doctors` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL UNIQUE,
  `doctor_name` VARCHAR(50) NOT NULL,
  `department` VARCHAR(50) NULL,
  `title_name` VARCHAR(50) NULL,
  `hospital_name` VARCHAR(100) NULL,
  `specialty` VARCHAR(255) NULL,
  `intro` TEXT NULL,
  `license_no` VARCHAR(100) NULL,
  `audit_status` VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  `audit_remark` VARCHAR(255) NULL,
  `service_status` INT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_doctors_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `admins` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL UNIQUE,
  `admin_name` VARCHAR(50) NOT NULL,
  `job_title` VARCHAR(50) NULL,
  `permissions_summary` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_admins_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `consultations` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `case_no` VARCHAR(50) NOT NULL UNIQUE,
  `user_id` BIGINT NOT NULL,
  `assigned_doctor_id` BIGINT NULL,
  `summary_title` VARCHAR(120) NULL,
  `chief_complaint` TEXT NULL,
  `onset_duration` VARCHAR(50) NULL,
  `itch_level` INT NULL,
  `pain_level` INT NULL,
  `spread_flag` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(30) NOT NULL DEFAULT 'PENDING_AI',
  `risk_level` VARCHAR(20) NULL,
  `ai_enabled` INT NOT NULL DEFAULT 1,
  `need_doctor_review` INT NOT NULL DEFAULT 1,
  `ai_confidence` FLOAT NULL,
  `submitted_at` DATETIME NULL,
  `closed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  `is_deleted` INT NOT NULL DEFAULT 0,
  CONSTRAINT `fk_consultations_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_consultations_assigned_doctor_id` FOREIGN KEY (`assigned_doctor_id`) REFERENCES `doctors` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `consultation_images` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `consultation_id` BIGINT NOT NULL,
  `file_name` VARCHAR(255) NOT NULL,
  `file_url` VARCHAR(2048) NOT NULL,
  `file_size` BIGINT NULL,
  `file_type` VARCHAR(50) NULL,
  `sort_no` INT NULL,
  `uploaded_at` DATETIME NOT NULL,
  CONSTRAINT `fk_consultation_images_consultation_id` FOREIGN KEY (`consultation_id`) REFERENCES `consultations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ai_analysis_records` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `consultation_id` BIGINT NOT NULL,
  `model_name` VARCHAR(100) NOT NULL,
  `prompt_version` VARCHAR(50) NULL,
  `input_summary` TEXT NULL,
  `image_observation` TEXT NULL,
  `possible_conditions` TEXT NULL,
  `risk_level` VARCHAR(20) NULL,
  `care_advice` TEXT NULL,
  `hospital_advice` TEXT NULL,
  `high_risk_alert` TEXT NULL,
  `disclaimer` VARCHAR(255) NULL,
  `raw_response` TEXT NULL,
  `analysis_status` VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
  `fail_reason` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_ai_analysis_records_consultation_id` FOREIGN KEY (`consultation_id`) REFERENCES `consultations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `consultation_messages` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `consultation_id` BIGINT NOT NULL,
  `sender_role` VARCHAR(20) NOT NULL,
  `sender_id` BIGINT NULL,
  `message_type` VARCHAR(20) NOT NULL DEFAULT 'TEXT',
  `content` TEXT NOT NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_consultation_messages_consultation_id` FOREIGN KEY (`consultation_id`) REFERENCES `consultations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `consultation_replies` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `consultation_id` BIGINT NOT NULL,
  `doctor_id` BIGINT NOT NULL,
  `content` TEXT NOT NULL,
  `suggest_offline_visit` INT NOT NULL DEFAULT 0,
  `suggest_follow_up` INT NOT NULL DEFAULT 0,
  `doctor_remark` TEXT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_consultation_replies_consultation_id` FOREIGN KEY (`consultation_id`) REFERENCES `consultations` (`id`),
  CONSTRAINT `fk_consultation_replies_doctor_id` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `qa_records` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `related_consultation_id` BIGINT NULL,
  `question_text` TEXT NOT NULL,
  `answer_text` TEXT NULL,
  `references_json` TEXT NULL,
  `risk_hint` VARCHAR(255) NULL,
  `answer_status` VARCHAR(20) NOT NULL DEFAULT 'SUCCESS',
  `model_name` VARCHAR(100) NULL,
  `fail_reason` VARCHAR(255) NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_qa_records_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_qa_records_related_consultation_id` FOREIGN KEY (`related_consultation_id`) REFERENCES `consultations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `knowledge_documents` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `doc_title` VARCHAR(255) NOT NULL,
  `category` VARCHAR(100) NULL,
  `tag_list` VARCHAR(255) NULL,
  `source_type` VARCHAR(50) NULL,
  `source_name` VARCHAR(255) NULL,
  `summary` TEXT NULL,
  `file_url` VARCHAR(500) NULL,
  `parse_status` VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
  `chunk_count` INT NOT NULL DEFAULT 0,
  `enabled_flag` INT NOT NULL DEFAULT 0,
  `uploaded_by` BIGINT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_knowledge_documents_uploaded_by` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `knowledge_chunks_metadata` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `document_id` BIGINT NOT NULL,
  `chunk_no` INT NOT NULL,
  `chunk_text` TEXT NOT NULL,
  `keywords` VARCHAR(255) NULL,
  `token_count` INT NULL,
  `enabled_flag` INT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_knowledge_chunks_metadata_document_id` FOREIGN KEY (`document_id`) REFERENCES `knowledge_documents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `system_configs` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `config_key` VARCHAR(100) NOT NULL UNIQUE,
  `config_value` TEXT NOT NULL,
  `config_group` VARCHAR(50) NULL,
  `description` VARCHAR(255) NULL,
  `updated_by` BIGINT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_system_configs_updated_by` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `announcements` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `title` VARCHAR(200) NOT NULL,
  `content` TEXT NOT NULL,
  `status` INT NOT NULL DEFAULT 1,
  `publish_scope` VARCHAR(50) NULL,
  `published_by` BIGINT NULL,
  `published_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_announcements_published_by` FOREIGN KEY (`published_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `notifications` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `title` VARCHAR(120) NOT NULL,
  `content` TEXT NOT NULL,
  `notification_type` VARCHAR(30) NOT NULL DEFAULT 'SYSTEM',
  `related_business_type` VARCHAR(30) NULL,
  `related_business_id` BIGINT NULL,
  `read_flag` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_notifications_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `doctor_ai_feedbacks` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `consultation_id` BIGINT NOT NULL,
  `doctor_id` BIGINT NOT NULL,
  `ai_accuracy` VARCHAR(20) NULL,
  `correction_note` TEXT NULL,
  `knowledge_gap_note` TEXT NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_doctor_ai_feedbacks_consultation_id` FOREIGN KEY (`consultation_id`) REFERENCES `consultations` (`id`),
  CONSTRAINT `fk_doctor_ai_feedbacks_doctor_id` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `operation_logs` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `account_id` BIGINT NULL,
  `role_type` VARCHAR(20) NULL,
  `module_name` VARCHAR(50) NOT NULL,
  `operation_type` VARCHAR(50) NOT NULL,
  `business_id` VARCHAR(100) NULL,
  `operation_desc` VARCHAR(255) NULL,
  `request_ip` VARCHAR(50) NULL,
  `operation_result` VARCHAR(20) NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_operation_logs_account_id` FOREIGN KEY (`account_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `statistics_snapshots` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `snapshot_date` DATE NOT NULL,
  `metric_key` VARCHAR(50) NOT NULL,
  `metric_value` FLOAT NOT NULL,
  `metric_group` VARCHAR(30) NULL,
  `created_at` DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def build_base_seed() -> str:
    base_time = datetime(2026, 3, 1, 9, 0, 0)
    user_names = [
        "林安然", "周予宁", "陈沐阳", "许知夏", "顾言初", "沈舒禾", "宋嘉柠", "唐若棠", "程景澄", "陆知遥",
        "夏星河", "韩清和", "阮静姝", "白以澄", "江沐言", "祁安歌", "乔书意", "叶念安", "梁轻舟", "苏予棠",
        "顾屿川", "秦时雨", "唐念初", "沈听澜", "纪星野", "叶舒然", "程若微", "梁听雪", "陆清栀", "许沐晨",
        "江知意", "白景安", "温知行", "林栖迟", "周清禾", "顾明栀", "宋听岚", "沈沐夏", "唐星语", "许安禾",
    ]
    doctor_names = ["陈思远", "赵闻舟", "王清禾", "李悠然", "何知礼", "顾静安", "徐景行", "苏南乔", "周闻夏", "赵宁远", "黄若川", "冯知行"]
    admin_names = ["周明哲", "林嘉禾", "宋知远"]
    cities = ["上海", "杭州", "苏州", "南京", "深圳", "广州", "成都", "武汉", "西安", "青岛"]
    occupations = ["产品经理", "设计师", "教师", "护士", "运营", "程序员", "研究生", "自由职业", "市场专员", "会计"]
    skin_types = ["干性", "油性", "混合性", "敏感性"]
    sensitivities = ["低敏", "中度敏感", "高度敏感"]
    sleep_patterns = ["规律", "偶尔熬夜", "频繁熬夜"]
    diet_preferences = ["清淡饮食", "偏甜偏辣", "高蛋白饮食", "外卖较多"]

    users = []
    profiles = []
    health_profiles = []
    for index, name in enumerate(user_names, start=1):
        created = base_time + timedelta(hours=index)
        users.append(
            {
                "username": f"user{index:02d}",
                "password_hash": hash_password(f"user{index:02d}"),
                "role_type": "USER",
                "phone": f"1380000{index:04d}",
                "email": f"user{index:02d}@dermaagent.local",
                "avatar_url": "",
                "status": 1 if index % 11 else 0,
                "last_login_at": created + timedelta(days=28),
                "created_at": created,
                "updated_at": created + timedelta(days=30),
                "is_deleted": 0,
            }
        )
        profiles.append(
            {
                "user_id": index,
                "real_name": name,
                "gender": "女" if index % 2 else "男",
                "age": 19 + index % 17,
                "birthday": date(1990 + index % 12, (index % 12) + 1, (index % 26) + 1),
                "city": cities[index % len(cities)],
                "occupation": occupations[index % len(occupations)],
                "emergency_contact": f"{name}家属",
                "emergency_phone": f"1390000{index:04d}",
                "remark": "近半年关注皮肤屏障修复与防晒。",
                "created_at": created,
                "updated_at": created + timedelta(days=15),
            }
        )
        health_profiles.append(
            {
                "user_profile_id": index,
                "allergy_history": "对酒精类消毒液轻度敏感" if index % 3 == 0 else "无明确药物过敏史",
                "past_medical_history": "有季节性过敏性鼻炎" if index % 4 == 0 else "无特殊既往病史",
                "medication_history": "近两周有外用保湿修护霜" if index % 2 else "近期未规律用药",
                "skin_type": skin_types[index % len(skin_types)],
                "skin_sensitivity": sensitivities[index % len(sensitivities)],
                "sleep_pattern": sleep_patterns[index % len(sleep_patterns)],
                "diet_preference": diet_preferences[index % len(diet_preferences)],
                "special_notes": "换季时面部容易发红发痒。" if index % 5 == 0 else "工作压力偏大，近期作息不稳定。",
                "updated_at": created + timedelta(days=16),
            }
        )

    for index, name in enumerate(doctor_names, start=1):
        user_id = 40 + index
        created = base_time + timedelta(days=1, hours=index)
        users.append(
            {
                "username": f"doctor{index:02d}",
                "password_hash": hash_password(f"doctor{index:02d}"),
                "role_type": "DOCTOR",
                "phone": f"1371000{index:04d}",
                "email": f"doctor{index:02d}@dermaagent.local",
                "avatar_url": "",
                "status": 1,
                "last_login_at": created + timedelta(days=26),
                "created_at": created,
                "updated_at": created + timedelta(days=28),
                "is_deleted": 0,
            }
        )
        profiles.append(
            {
                "user_id": user_id,
                "real_name": name,
                "gender": "男" if index % 2 else "女",
                "age": 30 + index,
                "birthday": date(1980 + index, (index % 12) + 1, (index % 20) + 1),
                "city": cities[(index + 3) % len(cities)],
                "occupation": "执业医师",
                "emergency_contact": f"{name}配偶",
                "emergency_phone": f"1362000{index:04d}",
                "remark": "可参与图文问诊与 AI 纠偏反馈。",
                "created_at": created,
                "updated_at": created + timedelta(days=20),
            }
        )

    for index, name in enumerate(admin_names, start=1):
        user_id = 52 + index
        created = base_time + timedelta(days=2, hours=index)
        users.append(
            {
                "username": f"admin{index:02d}",
                "password_hash": hash_password(f"admin{index:02d}"),
                "role_type": "ADMIN",
                "phone": f"1363000{index:04d}",
                "email": f"admin{index:02d}@dermaagent.local",
                "avatar_url": "",
                "status": 1,
                "last_login_at": created + timedelta(days=30),
                "created_at": created,
                "updated_at": created + timedelta(days=31),
                "is_deleted": 0,
            }
        )
        profiles.append(
            {
                "user_id": user_id,
                "real_name": name,
                "gender": "男",
                "age": 31 + index,
                "birthday": date(1988 + index, (index % 12) + 1, (index % 20) + 1),
                "city": cities[(index + 5) % len(cities)],
                "occupation": "平台管理",
                "emergency_contact": f"{name}同事",
                "emergency_phone": f"1354000{index:04d}",
                "remark": "负责平台配置、知识库与运营统计。",
                "created_at": created,
                "updated_at": created + timedelta(days=10),
            }
        )

    doctors = []
    for index, name in enumerate(doctor_names, start=1):
        created = base_time + timedelta(days=3, hours=index)
        doctors.append(
            {
                "user_id": 40 + index,
                "doctor_name": name,
                "department": "皮肤科",
                "title_name": ["主治医师", "副主任医师", "住院医师"][index % 3],
                "hospital_name": ["上海市第一人民医院", "杭州市第三人民医院", "南京鼓楼医院", "中山大学附属医院"][index % 4],
                "specialty": ["痤疮与敏感肌", "湿疹皮炎", "真菌感染", "银屑病与免疫皮肤病"][index % 4],
                "intro": f"{name} 擅长常见皮肤病图文问诊、慢病管理与长期随访。",
                "license_no": f"DRM2026{index:06d}",
                "audit_status": "APPROVED" if index <= 10 else ("PENDING" if index == 11 else "REJECTED"),
                "audit_remark": "资质齐全，允许接诊" if index <= 10 else ("待补充执业地点证明" if index == 11 else "上传证件不清晰"),
                "service_status": 1 if index <= 10 else 0,
                "created_at": created,
                "updated_at": created + timedelta(days=18),
            }
        )

    admins = []
    for index, name in enumerate(admin_names, start=1):
        created = base_time + timedelta(days=4, hours=index)
        admins.append(
            {
                "user_id": 52 + index,
                "admin_name": name,
                "job_title": ["平台运营负责人", "知识库管理员", "系统管理员"][index - 1],
                "permissions_summary": "用户管理、医生审核、知识库管理、日志统计",
                "created_at": created,
                "updated_at": created + timedelta(days=20),
            }
        )

    configs = [
        ("ai.mode", "mock", "AI", "AI 模式开关"),
        ("ai.default_model", "mock-qwen-vl", "AI", "默认视觉模型"),
        ("rag.mode", "mock", "RAG", "RAG 检索模式"),
        ("rag.top_k", "3", "RAG", "默认召回片段数"),
        ("consultation.auto_assign", "1", "CONSULTATION", "是否自动分配医生"),
        ("consultation.default_review", "1", "CONSULTATION", "默认需要医生复核"),
        ("upload.max_mb", "8", "FILE", "单张图片最大 MB"),
        ("security.jwt_expire_minutes", "720", "SECURITY", "JWT 过期时间"),
        ("dashboard.refresh_seconds", "30", "SYSTEM", "控制台刷新间隔"),
        ("knowledge.default_category", "皮肤疾病", "KNOWLEDGE", "默认知识分类"),
        ("notice.home_banner", "近期换季，请加强保湿、防晒并留意过敏源。", "CONTENT", "首页提示语"),
        ("support.hotline", "400-820-2026", "CONTENT", "客服热线"),
    ]
    system_configs = [
        {
            "config_key": key,
            "config_value": value,
            "config_group": group,
            "description": description,
            "updated_by": 53,
            "updated_at": base_time + timedelta(days=12, minutes=index),
        }
        for index, (key, value, group, description) in enumerate(configs, start=1)
    ]

    announcements = []
    for index, (title, content, scope) in enumerate(
        [
            ("春季敏感肌护理提醒", "近期花粉指数偏高，敏感肌用户建议减少功效叠加，优先修护屏障。", "ALL"),
            ("医生在线排班更新", "工作日 09:00-22:00 平台提供更快的医生图文复核响应。", "USER"),
            ("知识库已同步新版湿疹护理指南", "后台已更新常见湿疹、特应性皮炎与屏障修护相关知识内容。", "ADMIN"),
            ("系统安全与隐私提示", "请勿上传含有身份信息的图片，平台默认对病例进行脱敏展示。", "ALL"),
        ],
        start=1,
    ):
        created = base_time + timedelta(days=10 + index)
        announcements.append(
            {
                "title": title,
                "content": content,
                "status": 1,
                "publish_scope": scope,
                "published_by": 53,
                "published_at": created,
                "created_at": created,
                "updated_at": created,
            }
        )

    sql = ["SET NAMES utf8mb4;", f"USE `{DB_NAME}`;", ""]
    sql.append(build_insert("users", list(users[0].keys()), users))
    sql.append(build_insert("user_profiles", list(profiles[0].keys()), profiles))
    sql.append(build_insert("health_profiles", list(health_profiles[0].keys()), health_profiles))
    sql.append(build_insert("doctors", list(doctors[0].keys()), doctors))
    sql.append(build_insert("admins", list(admins[0].keys()), admins))
    sql.append(build_insert("system_configs", list(system_configs[0].keys()), system_configs))
    sql.append(build_insert("announcements", list(announcements[0].keys()), announcements))
    return "\n".join(sql)


def build_business_seed() -> str:
    base_time = datetime(2026, 3, 6, 10, 0, 0)
    complaints = [
        "面部反复长闭口和红色丘疹，最近两周明显增多",
        "脸颊发红发烫并伴有瘙痒，换了新护肤品后更明显",
        "手臂出现片状红斑并脱屑，洗澡后刺激感加重",
        "脚趾缝发白伴脱皮和瘙痒，运动后气味明显",
        "颈部起了小片湿疹样皮损，晚上瘙痒更重",
        "下巴周围长了脓疱样皮损，碰到有点疼",
        "额头和鼻翼反复出油并起粉刺，肤感粗糙",
        "小腿出现圆形红斑并逐渐扩大，边界清楚",
        "手背发干开裂并伴轻微刺痛，接触清洁剂后加重",
        "背部成片冒痘，出汗后更容易泛红",
        "面部两颊持续敏感泛红，伴轻度刺痒",
        "耳后局部皮肤破溃渗液，摸起来发热",
    ]
    onset_options = ["3天", "1周", "2周", "1个月", "反复半年", "近三天明显加重"]
    titles = ["面部痤疮倾向", "疑似接触性皮炎", "湿疹反复", "足部真菌困扰", "颈部湿疹样表现", "脓疱性皮损", "油脂分泌旺盛", "边界清晰红斑", "干裂屏障受损", "背部炎症痘痘", "面部敏感泛红", "破溃渗液高风险"]
    status_plan = ["CLOSED"] * 14 + ["DOCTOR_REPLIED"] * 18 + ["WAIT_DOCTOR"] * 18 + ["AI_DONE"] * 12 + ["PENDING_AI"] * 6 + ["FAILED"] * 4
    images = []
    consultations = []
    analysis_records = []
    messages = []
    replies = []
    qa_records = []
    docs = []
    chunks = []
    feedbacks = []
    notifications = []

    doc_titles = [
        "痤疮基础护理指南", "敏感肌屏障修护手册", "湿疹与特应性皮炎护理建议", "脚气与真菌感染家庭护理",
        "脂溢性皮炎识别要点", "玫瑰痤疮生活管理建议", "银屑病长期管理说明", "儿童湿疹家属照护建议",
        "手部皮炎职业暴露防护", "带状疱疹就医提醒", "色素沉着恢复期护理", "防晒与光敏反应说明",
        "激素依赖性皮炎风险提示", "毛囊炎日常管理", "汗疱疹护理策略", "荨麻疹诱因排查建议",
        "头皮屑与脂溢性头皮管理", "季节性干痒修护方案", "换季屏障修护策略", "青春期痘痘饮食建议",
        "孕期皮肤不适就医建议", "医美后修护注意事项", "皮肤清洁误区清单", "常见外用药使用提醒",
    ]
    categories = ["痤疮", "敏感肌", "湿疹", "真菌感染", "炎症皮肤病", "护理指南"]

    for index, title in enumerate(doc_titles, start=1):
        created = base_time + timedelta(days=index // 3, minutes=index * 8)
        parse_status = "ENABLED" if index <= 14 else ("EMBEDDED" if index <= 20 else "CHUNKED")
        enabled_flag = 1 if index <= 18 else 0
        docs.append(
            {
                "doc_title": title,
                "category": categories[index % len(categories)],
                "tag_list": "保湿,屏障,线下就医,皮肤管理",
                "source_type": "UPLOAD",
                "source_name": f"knowledge-{index:02d}.pdf",
                "summary": f"{title} 覆盖诱因判断、基础护理、风险识别与线下就医提醒。",
                "file_url": f"/uploads/knowledge/knowledge-{index:02d}.pdf",
                "parse_status": parse_status,
                "chunk_count": 4,
                "enabled_flag": enabled_flag,
                "uploaded_by": 53,
                "created_at": created,
                "updated_at": created + timedelta(hours=4),
            }
        )
        for chunk_no in range(1, 5):
            text = [
                f"{title} 建议先识别诱因、部位、时长以及是否伴随瘙痒或疼痛。",
                f"{title} 日常护理应以温和清洁、及时保湿和减少刺激为核心。",
                f"{title} 若出现渗液、发热、破溃、迅速扩散或夜间症状明显加重，应尽快线下就医。",
                f"{title} 就诊时建议携带近期照片、过敏史和近两周外用药与护肤品使用记录。",
            ][chunk_no - 1]
            chunks.append(
                {
                    "document_id": index,
                    "chunk_no": chunk_no,
                    "chunk_text": text,
                    "keywords": f"{categories[index % len(categories)]},保湿,就医,护理",
                    "token_count": len(text),
                    "enabled_flag": enabled_flag,
                    "created_at": created + timedelta(minutes=chunk_no),
                }
            )

    for index in range(1, 73):
        created = base_time + timedelta(hours=index * 4)
        status = status_plan[index - 1]
        complaint = complaints[(index - 1) % len(complaints)]
        title = titles[(index - 1) % len(titles)]
        risk_level = "HIGH" if index % 9 == 0 or "破溃" in complaint else ("MEDIUM" if index % 2 == 0 else "LOW")
        assigned_doctor = ((index - 1) % 10) + 1
        consultations.append(
            {
                "case_no": f"CASE202603{index:04d}",
                "user_id": ((index - 1) % 40) + 1,
                "assigned_doctor_id": assigned_doctor,
                "summary_title": title,
                "chief_complaint": complaint,
                "onset_duration": onset_options[index % len(onset_options)],
                "itch_level": index % 5 + (1 if risk_level != "LOW" else 0),
                "pain_level": (index + 2) % 4 + (1 if risk_level == "HIGH" else 0),
                "spread_flag": 1 if index % 4 == 0 else 0,
                "status": status,
                "risk_level": risk_level,
                "ai_enabled": 1,
                "need_doctor_review": 1,
                "ai_confidence": round(0.63 + (index % 8) * 0.03, 2) if status != "FAILED" else 0.41,
                "submitted_at": created,
                "closed_at": created + timedelta(days=2) if status == "CLOSED" else None,
                "created_at": created,
                "updated_at": created + timedelta(hours=6),
                "is_deleted": 0,
            }
        )

        images.append(
            {
                "consultation_id": index,
                "file_name": f"case-{index:03d}-main.svg",
                "file_url": svg_data_uri(f"CASE {index:03d}", "#0F766E", "#16324F"),
                "file_size": 1280 + index,
                "file_type": "image/svg+xml",
                "sort_no": 1,
                "uploaded_at": created,
            }
        )
        if index % 2 == 0:
            images.append(
                {
                    "consultation_id": index,
                    "file_name": f"case-{index:03d}-detail.svg",
                    "file_url": svg_data_uri(f"DETAIL {index:03d}", "#1D4ED8", "#0B1120"),
                    "file_size": 1320 + index,
                    "file_type": "image/svg+xml",
                    "sort_no": 2,
                    "uploaded_at": created + timedelta(minutes=5),
                }
            )

        messages.append(
            {
                "consultation_id": index,
                "sender_role": "USER",
                "sender_id": ((index - 1) % 40) + 1,
                "message_type": "TEXT",
                "content": complaint,
                "created_at": created,
            }
        )

        if status != "PENDING_AI":
            analysis_status = "FAIL" if status == "FAILED" else "SUCCESS"
            analysis_records.append(
                {
                    "consultation_id": index,
                    "model_name": "mock-qwen-vl",
                    "prompt_version": "v1.0.0",
                    "input_summary": f"{complaint} | 用户提供 1-2 张皮肤图片",
                    "image_observation": "图像可见局部红斑、丘疹或脱屑表现，建议结合病史判断。",
                    "possible_conditions": "痤疮、接触性皮炎、湿疹、毛囊炎、真菌感染等常见皮肤问题方向" if analysis_status == "SUCCESS" else "",
                    "risk_level": risk_level if analysis_status == "SUCCESS" else "HIGH",
                    "care_advice": "优先采取温和清洁、加强保湿、减少抓挠与刺激性护肤品叠加。" if analysis_status == "SUCCESS" else "",
                    "hospital_advice": "若症状持续加重、范围扩大或伴渗液发热，请尽快线下皮肤科面诊。" if analysis_status == "SUCCESS" else "",
                    "high_risk_alert": "高风险就医提醒：出现明显红肿热痛、流脓、发热或迅速扩散时，应立即线下就医。",
                    "disclaimer": "医疗辅助免责声明：本结果仅供健康参考，不能替代医生面诊与医学诊断。",
                    "raw_response": json.dumps({"case_no": f"CASE202603{index:04d}", "mock": True}, ensure_ascii=False),
                    "analysis_status": analysis_status,
                    "fail_reason": "图片质量不足，已建议重新上传清晰图片" if analysis_status == "FAIL" else None,
                    "created_at": created + timedelta(minutes=18),
                }
            )

        if status in {"DOCTOR_REPLIED", "CLOSED"}:
            reply_time = created + timedelta(hours=9)
            replies.append(
                {
                    "consultation_id": index,
                    "doctor_id": assigned_doctor,
                    "content": "结合图片和描述，当前更像常见炎症性皮肤问题，建议先避免刺激、规律保湿，必要时线下面诊复核。",
                    "suggest_offline_visit": 1 if risk_level == "HIGH" else 0,
                    "suggest_follow_up": 1,
                    "doctor_remark": "建议 3-5 天内继续观察，若加重及时复诊。",
                    "created_at": reply_time,
                    "updated_at": reply_time,
                }
            )
            messages.append(
                {
                    "consultation_id": index,
                    "sender_role": "DOCTOR",
                    "sender_id": 40 + assigned_doctor,
                    "message_type": "TEXT",
                    "content": "已查看 AI 结果和图片，建议按医嘱做好修护和观察。",
                    "created_at": reply_time,
                }
            )
            if index % 4 == 0:
                messages.append(
                    {
                        "consultation_id": index,
                        "sender_role": "USER",
                        "sender_id": ((index - 1) % 40) + 1,
                        "message_type": "TEXT",
                        "content": "收到，已暂停新护肤品并观察变化。",
                        "created_at": reply_time + timedelta(hours=3),
                    }
                )

        if status in {"DOCTOR_REPLIED", "CLOSED", "WAIT_DOCTOR"} and index % 2 == 0:
            feedbacks.append(
                {
                    "consultation_id": index,
                    "doctor_id": assigned_doctor,
                    "ai_accuracy": ["HIGH", "MEDIUM", "LOW"][index % 3],
                    "correction_note": "AI 对风险判断较敏感，建议补充诱因与近期用药信息。",
                    "knowledge_gap_note": "可补充敏感肌、职业性手部皮炎与真菌感染鉴别内容。",
                    "created_at": created + timedelta(hours=10),
                }
            )

        notifications.append(
            {
                "user_id": ((index - 1) % 40) + 1,
                "title": "问诊状态更新",
                "content": f"问诊单 CASE202603{index:04d} 当前状态为 {status}。",
                "notification_type": "CONSULTATION",
                "related_business_type": "CONSULTATION",
                "related_business_id": index,
                "read_flag": 0 if index % 3 else 1,
                "created_at": created + timedelta(hours=1),
            }
        )
        if status in {"WAIT_DOCTOR", "DOCTOR_REPLIED"}:
            notifications.append(
                {
                    "user_id": 40 + assigned_doctor,
                    "title": "新的待处理病例",
                    "content": f"CASE202603{index:04d} 已进入你的待处理列表。",
                    "notification_type": "CONSULTATION",
                    "related_business_type": "CONSULTATION",
                    "related_business_id": index,
                    "read_flag": 0 if index % 5 else 1,
                    "created_at": created + timedelta(hours=2),
                }
            )

    question_bank = [
        "痘痘反复长是不是和熬夜有关？",
        "脸上过敏泛红时可以继续刷酸吗？",
        "湿疹反复瘙痒应该怎样护理？",
        "脚气脱皮需要注意什么？",
        "屏障受损时护肤步骤应该怎么减法？",
        "面部刺痛泛红是不是敏感肌？",
        "背部痘痘需要怎么清洁和护理？",
        "真菌感染会不会传染给家人？",
        "手部皮炎接触清洁剂后更严重怎么办？",
        "如果出现渗液破溃需要立刻去医院吗？",
    ]
    for index in range(1, 61):
        created = base_time + timedelta(days=index % 18, hours=index % 9)
        question = question_bank[(index - 1) % len(question_bank)]
        refs = [
            {"document_id": ((index - 1) % 24) + 1, "document_title": doc_titles[(index - 1) % len(doc_titles)], "chunk_id": ((index - 1) % 96) + 1, "score": 9 - index % 3},
            {"document_id": (index % 24) + 1, "document_title": doc_titles[index % len(doc_titles)], "chunk_id": (index % 96) + 1, "score": 7 - index % 2},
        ]
        qa_records.append(
            {
                "user_id": ((index - 1) % 30) + 1,
                "related_consultation_id": ((index - 1) % 72) + 1,
                "question_text": question,
                "answer_text": "建议先从减少刺激、温和清洁、持续保湿和记录变化做起。如伴发热、渗液、迅速扩散或反复不缓解，请尽快线下就医。医疗辅助免责声明：本回答仅供健康参考，不作诊断结论。",
                "references_json": json.dumps(refs, ensure_ascii=False),
                "risk_hint": "若伴明显疼痛、渗液、发热或范围扩大，请及时线下就医。",
                "answer_status": "SUCCESS",
                "model_name": "mock-rag",
                "fail_reason": None,
                "created_at": created,
            }
        )

    sql = ["SET NAMES utf8mb4;", f"USE `{DB_NAME}`;", ""]
    sql.append(build_insert("knowledge_documents", list(docs[0].keys()), docs))
    sql.append(build_insert("knowledge_chunks_metadata", list(chunks[0].keys()), chunks))
    sql.append(build_insert("consultations", list(consultations[0].keys()), consultations))
    sql.append(build_insert("consultation_images", list(images[0].keys()), images))
    sql.append(build_insert("ai_analysis_records", list(analysis_records[0].keys()), analysis_records))
    sql.append(build_insert("consultation_messages", list(messages[0].keys()), messages))
    sql.append(build_insert("consultation_replies", list(replies[0].keys()), replies))
    sql.append(build_insert("qa_records", list(qa_records[0].keys()), qa_records))
    sql.append(build_insert("doctor_ai_feedbacks", list(feedbacks[0].keys()), feedbacks))
    sql.append(build_insert("notifications", list(notifications[0].keys()), notifications))
    return "\n".join(sql)


def build_stats_seed() -> str:
    base_time = datetime(2026, 3, 10, 8, 0, 0)
    logs = []
    stats = []
    modules = [
        ("AUTH", "LOGIN", "账号登录"),
        ("CONSULTATION", "CREATE", "提交图文问诊"),
        ("AI", "ANALYZE", "执行 AI 图文辅助分析"),
        ("DOCTOR", "REPLY", "医生回复问诊"),
        ("RAG", "QA", "发起知识问答"),
        ("KNOWLEDGE", "CHUNK", "切分知识文档"),
        ("CONFIG", "UPDATE", "更新系统配置"),
    ]
    for index in range(1, 151):
        module_name, operation_type, desc = modules[(index - 1) % len(modules)]
        role_type = ["USER", "DOCTOR", "ADMIN"][index % 3]
        if role_type == "USER":
            account_id = ((index - 1) % 40) + 1
        elif role_type == "DOCTOR":
            account_id = 40 + ((index - 1) % 12) + 1
        else:
            account_id = 53 + (index % 3)
        created = base_time + timedelta(hours=index)
        logs.append(
            {
                "account_id": account_id,
                "role_type": role_type,
                "module_name": module_name,
                "operation_type": operation_type,
                "business_id": str(((index - 1) % 72) + 1),
                "operation_desc": desc,
                "request_ip": f"127.0.0.{(index % 80) + 1}",
                "operation_result": "FAIL" if index % 29 == 0 else "SUCCESS",
                "created_at": created,
            }
        )

    for day_index in range(30):
        snap_date = date(2026, 3, 17) + timedelta(days=day_index)
        stats.extend(
            [
                {
                    "snapshot_date": snap_date,
                    "metric_key": "consultation_total",
                    "metric_value": 42 + day_index * 1.8,
                    "metric_group": "consultation",
                    "created_at": datetime.combine(snap_date, datetime.min.time()) + timedelta(hours=1),
                },
                {
                    "snapshot_date": snap_date,
                    "metric_key": "high_risk_total",
                    "metric_value": 6 + day_index * 0.3,
                    "metric_group": "consultation",
                    "created_at": datetime.combine(snap_date, datetime.min.time()) + timedelta(hours=1),
                },
                {
                    "snapshot_date": snap_date,
                    "metric_key": "qa_total",
                    "metric_value": 28 + day_index * 1.2,
                    "metric_group": "qa",
                    "created_at": datetime.combine(snap_date, datetime.min.time()) + timedelta(hours=1),
                },
            ]
        )

    sql = ["SET NAMES utf8mb4;", f"USE `{DB_NAME}`;", ""]
    sql.append(build_insert("operation_logs", list(logs[0].keys()), logs))
    sql.append(build_insert("statistics_snapshots", list(stats[0].keys()), stats))
    return "\n".join(sql)


def main() -> None:
    outputs = {
        "01_schema.sql": build_schema(),
        "02_seed_base.sql": build_base_seed(),
        "03_seed_business.sql": build_business_seed(),
        "04_seed_stats.sql": build_stats_seed(),
    }
    for name, content in outputs.items():
        (ROOT / name).write_text(content, encoding="utf-8")
    print("generated", ", ".join(outputs))


if __name__ == "__main__":
    main()
