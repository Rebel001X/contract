# 点踩接口API文档（包含合同ID字段）

## 概述

点踩接口用于用户对审查规则结果进行反馈，支持点赞/点踩、反馈建议、审核状态和合同ID管理。

## 接口信息

### 用户反馈接口

**接口路径**: `POST /api/confirm-review-rule-result/feedback`

**功能描述**: 对审查规则结果进行用户反馈，支持点赞/点踩、反馈建议、审核状态和合同ID

**请求参数**:

```json
{
  "rule_id": 1,
  "feedback": 1,
  "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
  "is_approved": true,
  "contract_id": "CONTRACT_001"
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `rule_id` | int | 是 | 规则ID |
| `feedback` | int | 是 | 用户反馈: 0=点踩, 1=点赞 |
| `feedback_suggestion` | string | 否 | 反馈建议内容 |
| `is_approved` | boolean | 否 | 审核是否通过标志 |
| `contract_id` | string | 否 | 合同ID |

**响应示例**:

```json
{
  "code": 200,
  "message": "点赞成功",
  "user_feedback": 1,
  "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
  "is_approved": true,
  "contract_id": "CONTRACT_001",
  "rule_id": 1,
  "id": 5
}
```

## 使用示例

### 1. 点赞 + 反馈建议 + 审核通过 + 合同ID

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 1,
    "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
    "is_approved": true,
    "contract_id": "CONTRACT_001"
  }'
```

### 2. 点踩 + 反馈建议 + 审核不通过 + 合同ID

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 0,
    "feedback_suggestion": "这个规则分析有误，需要重新评估",
    "is_approved": false,
    "contract_id": "CONTRACT_002"
  }'
```

### 3. 只更新合同ID

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 1,
    "contract_id": "CONTRACT_003"
  }'
```

## 数据库字段

### confirm_review_rule_result 表新增字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `feedback_suggestion` | TEXT | 反馈建议内容 |
| `is_approved` | BOOLEAN | 审核是否通过标志 |
| `contract_id` | VARCHAR(255) | 合同ID |

### SQL语句

```sql
-- 添加反馈建议字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `feedback_suggestion` TEXT NULL COMMENT '反馈建议内容' 
AFTER `user_feedback`;

-- 添加审核是否通过标志字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `is_approved` BOOLEAN NULL COMMENT '审核是否通过标志' 
AFTER `feedback_suggestion`;

-- 添加合同ID字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `contract_id` VARCHAR(255) NULL COMMENT '合同ID' 
AFTER `is_approved`;
```

## 功能特点

1. **灵活的参数支持**: 所有新增字段都是可选的，可以单独更新
2. **向后兼容**: 不影响现有的点赞/点踩功能
3. **数据完整性**: 支持反馈建议、审核状态和合同ID的完整记录
4. **查询支持**: 可以通过合同ID进行数据查询和统计

## 错误处理

- **400**: 缺少必填参数 `rule_id` 或 `feedback`
- **404**: 规则结果不存在
- **500**: 服务器内部错误

## 测试

运行测试脚本验证功能：

```bash
python test_feedback_with_contract_id.py
``` 