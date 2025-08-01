-- 添加审计质量评分字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `audit_quality` INT NULL COMMENT '审计质量评分(1-5分)' 
AFTER `error_type`; 