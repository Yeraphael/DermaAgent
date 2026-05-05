USE `derma_agent`;

ALTER TABLE `consultations`
  ADD COLUMN `abnormal_flag` INT NOT NULL DEFAULT 0 AFTER `ai_confidence`,
  ADD COLUMN `abnormal_note` TEXT NULL AFTER `abnormal_flag`,
  ADD COLUMN `archived_flag` INT NOT NULL DEFAULT 0 AFTER `abnormal_note`,
  ADD COLUMN `archived_at` DATETIME NULL AFTER `archived_flag`;

ALTER TABLE `consultation_replies`
  ADD COLUMN `first_impression` TEXT NULL AFTER `content`,
  ADD COLUMN `care_advice` TEXT NULL AFTER `first_impression`;
