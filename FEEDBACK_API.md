# 点踩接口API文档

## 概述

点踩接口用于用户对审查规则结果进行反馈，支持点赞/点踩、反馈建议和审核状态管理。

## 接口信息

### 用户反馈接口

**接口路径**: `POST /api/confirm-review-rule-result/feedback`

**功能描述**: 对审查规则结果进行用户反馈，支持点赞/点踩、反馈建议和审核状态

**请求参数**:

```json
{
  "rule_id": 1,
  "feedback": 1,
  "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
  "is_approved": true
}
```

**字段说明**:

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `rule_id` | int | 是 | 规则ID |
| `feedback` | int | 是 | 用户反馈: 0=点踩, 1=点赞 |
| `feedback_suggestion` | string | 否 | 反馈建议内容 |
| `is_approved` | boolean | 否 | 审核是否通过标志 |

**响应示例**:

```json
{
  "code": 200,
  "message": "点赞成功",
  "user_feedback": 1,
  "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
  "is_approved": true,
  "rule_id": 1,
  "id": 5
}
```

## 使用示例

### 1. 点赞 + 反馈建议 + 审核通过

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 1,
    "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
    "is_approved": true
  }'
```

### 2. 点踩 + 反馈建议 + 审核不通过

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 0,
    "feedback_suggestion": "这个规则分析有误，需要重新审查",
    "is_approved": false
  }'
```

### 3. 只点赞，不提供其他字段

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 1
  }'
```

## 数据库字段

### ConfirmReviewRuleResult 表新增字段

```sql
-- 反馈建议字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `feedback_suggestion` TEXT NULL COMMENT '反馈建议内容' 
AFTER `user_feedback`;

-- 审核是否通过标志字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `is_approved` BOOLEAN NULL COMMENT '审核是否通过标志' 
AFTER `feedback_suggestion`;
```

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `user_feedback` | int | 用户反馈(0=点踩, 1=点赞, null=无反馈) |
| `feedback_suggestion` | text | 反馈建议内容 |
| `is_approved` | boolean | 审核是否通过标志 |

## 错误处理

### 400 错误 - 参数错误

```json
{
  "detail": "必须提供 rule_id 和 feedback(0或1)"
}
```

### 404 错误 - 规则不存在

```json
{
  "detail": "规则结果不存在"
}
```

## 查询包含新字段的数据

### 分页查询接口

**接口路径**: `GET /api/confirm-review-rule-result/page`

**查询参数**:
- `skip`: 跳过记录数（默认0）
- `limit`: 每页数量（默认20，最大100）
- `rule_id`: 规则ID过滤（可选）
- `session_id`: 会话ID过滤（可选）
- `review_result`: 审查结果过滤（可选）

**响应示例**:

```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "session_id": "session_123",
      "rule_id": 1,
      "rule_name": "合同主体审查",
      "rule_index": 0,
      "review_result": "FAIL",
      "risk_level": "high",
      "matched_content": "合同内容片段",
      "analysis": "详细分析说明",
      "issues": ["问题1", "问题2"],
      "suggestions": ["建议1", "建议2"],
      "confidence_score": 80,
      "user_feedback": 1,
      "feedback_suggestion": "这个规则分析得很准确",
      "is_approved": true,
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

## 测试

运行测试脚本验证功能：

```bash
cd rag642
python test_feedback_api.py
```

## 更新日志

### v1.1.0 (2024-01-01)
- ✅ 新增 `feedback_suggestion` 字段，支持用户反馈建议
- ✅ 新增 `is_approved` 字段，支持审核状态管理
- ✅ 更新点踩接口，支持新字段的更新
- ✅ 更新查询接口，返回新字段数据
- ✅ 添加完整的测试用例 