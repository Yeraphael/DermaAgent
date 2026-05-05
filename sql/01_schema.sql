SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS `derma_agent` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `derma_agent`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `statistics_snapshots`;
DROP TABLE IF EXISTS `operation_logs`;
DROP TABLE IF EXISTS `doctor_ai_feedbacks`;
DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `announcements`;
DROP TABLE IF EXISTS `system_configs`;
DROP TABLE IF EXISTS `tool_call_logs`;
DROP TABLE IF EXISTS `chat_messages`;
DROP TABLE IF EXISTS `chat_sessions`;
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
  `abnormal_flag` INT NOT NULL DEFAULT 0,
  `abnormal_note` TEXT NULL,
  `archived_flag` INT NOT NULL DEFAULT 0,
  `archived_at` DATETIME NULL,
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
  `first_impression` TEXT NULL,
  `care_advice` TEXT NULL,
  `suggest_offline_visit` INT NOT NULL DEFAULT 0,
  `suggest_follow_up` INT NOT NULL DEFAULT 0,
  `doctor_remark` TEXT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_consultation_replies_consultation_id` FOREIGN KEY (`consultation_id`) REFERENCES `consultations` (`id`),
  CONSTRAINT `fk_consultation_replies_doctor_id` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `chat_sessions` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `title` VARCHAR(120) NOT NULL,
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL,
  CONSTRAINT `fk_chat_sessions_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `chat_messages` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `session_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `role` VARCHAR(20) NOT NULL,
  `content` TEXT NOT NULL,
  `intent` VARCHAR(30) NULL,
  `used_tool` INT NOT NULL DEFAULT 0,
  `tool_name` VARCHAR(50) NULL,
  `sources_json` TEXT NULL,
  `model_name` VARCHAR(100) NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_chat_messages_session_id` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`),
  CONSTRAINT `fk_chat_messages_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `tool_call_logs` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `session_id` BIGINT NOT NULL,
  `message_id` BIGINT NULL,
  `tool_name` VARCHAR(50) NOT NULL,
  `query` TEXT NOT NULL,
  `result_json` TEXT NULL,
  `latency_ms` INT NULL,
  `success` INT NOT NULL DEFAULT 1,
  `error_message` TEXT NULL,
  `created_at` DATETIME NOT NULL,
  CONSTRAINT `fk_tool_call_logs_session_id` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`),
  CONSTRAINT `fk_tool_call_logs_message_id` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`)
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
