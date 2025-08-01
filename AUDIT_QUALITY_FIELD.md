# Audit Quality 字段功能说明

## 概述

`audit_quality` 字段用于记录用户对审计质量的评分，支持1-5分的评分系统。

## 字段定义

### 数据库字段
```sql
-- 添加审计质量评分字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `audit_quality` INT NULL COMMENT '审计质量评分(1-5分)' 
AFTER `error_type`;
```

### 字段属性
- **字段名**: `audit_quality`
- **类型**: `INT`
- **范围**: 1-5分
- **默认值**: `NULL`（可选字段）
- **说明**: 审计质量评分(1-5分)

## API接口支持

### 1. Feedback接口支持

**接口路径**: `POST /api/confirm-review-rule-result/feedback`

**请求参数**:
```json
{
  "rule_id": 1,
  "feedback": 1,
  "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
  "is_approved": true,
  "contract_id": "CONTRACT_001",
  "manual_correction_en": "Manual correction in English",
  "error_type": "原文定位不准",
  "audit_quality": 5  // 新增字段：审计质量评分(1-5分)
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "点赞成功",
  "user_feedback": 1,
  "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
  "is_approved": true,
  "manual_correction_en": "Manual correction in English",
  "error_type": "原文定位不准",
  "audit_quality": 5,  // 新增字段
  "rule_id": 1,
  "id": 5
}
```

### 2. 查询接口支持

所有查询接口都会返回 `audit_quality` 字段：

**查询接口**: `GET /api/confirm-review-rule-results`

**响应示例**:
```json
{
  "items": [
    {
      "id": 1,
      "session_id": "session_123",
      "rule_id": 1,
      "rule_name": "合同主体审查",
      "review_result": "FAIL",
      "risk_level": "high",
      "user_feedback": 1,
      "feedback_suggestion": "这个规则分析得很准确",
      "is_approved": true,
      "manual_correction_en": "Manual correction",
      "error_type": "原文定位不准",
      "audit_quality": 5,  // 新增字段
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### 3. 分页查询接口支持

**分页查询接口**: `GET /api/confirm-review-rule-results/page`

**查询参数**:
- `page`: 页码（从1开始）
- `pageSize`: 每页数量（1-100）
- `rule_id`: 规则ID过滤（可选）
- `session_id`: 会话ID过滤（可选）
- `review_result`: 审查结果过滤（可选）
- `risk_level`: 风险等级过滤（可选）
- `contract_id`: 合同ID过滤（可选）
- `keyword`: 关键字模糊搜索（可选）

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "session_id": "session_123",
      "rule_id": 1,
      "rule_name": "合同主体审查",
      "rule_index": 0,
      "review_result": "FAIL",
      "risk_level": "high",
      "matched_content": ["合同内容片段"],
      "analysis": ["详细分析说明"],
      "issues": ["问题1", "问题2"],
      "suggestions": ["建议1", "建议2"],
      "confidence_score": 80,
      "user_feedback": 1,
      "feedback_suggestion": "这个规则分析得很准确",
      "is_approved": true,
      "contract_id": "CONTRACT_001",
      "contract_name": "测试合同",
      "risk_attribution_id": 1,
      "contract_type": "采购合同",
      "risk_attribution_name": "财务风险",
      "manual_correction_en": "Manual correction in English",
      "error_type": "原文定位不准",
      "audit_quality": 5,  // 新增字段：审计质量评分
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "maxPage": 10,
  "message": "",
  "total": 100
}
```

## 使用示例

### 1. 包含审计质量评分的点赞

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 1,
    "feedback_suggestion": "这个规则分析得很准确，建议继续保持",
    "is_approved": true,
    "contract_id": "CONTRACT_001",
    "manual_correction_en": "Manual correction in English",
    "error_type": "原文定位不准",
    "audit_quality": 5
  }'
```

### 2. 包含审计质量评分的点踩

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 0,
    "feedback_suggestion": "这个规则分析有误，需要重新审查",
    "is_approved": false,
    "contract_id": "CONTRACT_002",
    "manual_correction_en": "Another manual correction",
    "error_type": "审查推理错误",
    "audit_quality": 2
  }'
```

### 3. 只更新审计质量评分

```bash
curl -X POST "http://localhost:8001/api/confirm-review-rule-result/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": 1,
    "feedback": 1,
    "audit_quality": 4
  }'
```

## 评分标准建议

### 1分 - 很差
- 审计结果完全不准确
- 遗漏重要风险点
- 分析逻辑错误

### 2分 - 较差
- 审计结果基本不准确
- 存在明显错误
- 需要大幅改进

### 3分 - 一般
- 审计结果部分准确
- 存在一些错误
- 需要一定改进

### 4分 - 良好
- 审计结果基本准确
- 分析逻辑清晰
- 只有小问题

### 5分 - 优秀
- 审计结果非常准确
- 分析全面深入
- 建议很有价值

## 验证规则

- **范围验证**: 只接受1-5的整数值
- **类型验证**: 必须是整数类型
- **可选字段**: 可以不提供该字段

## 测试

运行测试脚本验证功能：

```bash
python test_audit_quality_feedback.py
```

## 数据库迁移

执行以下SQL语句添加字段：

```bash
mysql -u username -p database_name < add_audit_quality_field.sql
```

## 更新日志

### v1.2.0 (2024-01-01)
- ✅ 新增 `audit_quality` 字段，支持1-5分审计质量评分
- ✅ 更新feedback接口，支持audit_quality字段的输入和输出
- ✅ 更新查询接口，返回audit_quality字段
- ✅ 添加完整的测试用例
- ✅ 添加数据库迁移脚本 