-- 为 confirm_review_rule_result 表添加新字段
-- 执行时间: 2024-01-01

-- 添加反馈建议字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `feedback_suggestion` TEXT NULL COMMENT '反馈建议内容' 
AFTER `user_feedback`;

-- 添加审核是否通过标志字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `is_approved` BOOLEAN NULL COMMENT '审核是否通过标志' 
AFTER `feedback_suggestion`;

-- 验证字段是否添加成功
DESCRIBE `confirm_review_rule_result`; 