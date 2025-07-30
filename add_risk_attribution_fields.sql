-- 为 confirm_review_rule_result 表添加风险归属相关字段
-- 执行时间: 2024-01-01

-- 添加风险归属ID字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `risk_attribution_id` INT NULL COMMENT '风险归属ID' 
AFTER `contract_name`;

-- 添加风险归属名字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `risk_attribution_name` VARCHAR(255) NULL COMMENT '风险归属名' 
AFTER `risk_attribution_id`;

-- 添加人工修正英文字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `manual_correction_en` VARCHAR(500) NULL COMMENT '人工修正英文' 
AFTER `risk_attribution_name`;

-- 添加错误类型字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `error_type` ENUM('原文定位不准','原文检索错误','审查推理错误','遗漏风险') NULL COMMENT '错误类型' 
AFTER `manual_correction_en`;

-- 验证字段是否添加成功
DESCRIBE `confirm_review_rule_result`; 