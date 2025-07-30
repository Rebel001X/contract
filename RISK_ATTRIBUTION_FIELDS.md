# Risk Attribution 字段处理流程

## 概述

本文档描述了 `/chat/confirm` 接口中 `risk_attribution_id` 和 `risk_attribution_name` 字段的完整处理流程，从前端输入到数据库存储再到前端返回。

## 字段定义

- `risk_attribution_id`: 风险归属ID，整数类型，可为空
- `risk_attribution_name`: 风险归属名称，字符串类型，可为空

## 处理流程

### 1. 前端输入处理

前端可以通过以下两种命名风格传递字段：
- camelCase: `riskAttributionId`, `riskAttributionName`
- snake_case: `risk_attribution_id`, `risk_attribution_name`

```javascript
// 前端示例
{
  "review_rules": [
    {
      "id": 1,
      "ruleName": "付款条款审查",
      "riskAttributionId": 101,
      "riskAttributionName": "财务部",
      // 或者使用 snake_case
      "risk_attribution_id": 101,
      "risk_attribution_name": "财务部"
    }
  ]
}
```

### 2. 后端数据解析

在 `/chat/confirm` 接口中，后端会兼容两种命名风格：

```python
# 兼容驼峰和下划线字段名
risk_attribution_name = rule.get('risk_attribution_name') or rule.get('riskAttributionName') or '未知归属'
risk_attribution_id = rule.get('risk_attribution_id') or rule.get('riskAttributionId')
```

### 3. LLM 提示词构建

风险归属信息会被包含在发送给大语言模型的提示词中：

```python
rule_prompt = f"""
审查规则信息：
- 规则名称：{rule_name}
- 规则类型：{rule_type}
- 风险等级：{risk_level}
- 风险归属：{risk_attribution_name}  # 包含在提示词中
- 规则分组：{rule_group_name}
- 修改意见：{revise_opinion}
"""
```

### 4. LLM 输出格式

要求 LLM 在 JSON 输出中包含风险归属字段：

```json
{
    "rule_id": 1,
    "rule_name": "付款条款审查",
    "review_result": "不通过",
    "risk_level": "high",
    "risk_attribution_id": 101,
    "risk_attribution_name": "财务部",
    "matched_content": "匹配到的合同内容片段",
    "analysis": "详细的分析说明",
    "issues": ["具体问题描述"],
    "suggestions": ["具体建议"],
    "confidence_score": 0.85
}
```

### 5. 数据库存储

在保存到数据库时，会优先使用 LLM 返回的值，如果没有则使用前端传入的值：

```python
result_data = {
    # 新增：存 risk_attribution_id，优先取 rule_result，再取 rule_id_to_rule
    'risk_attribution_id': (
        rule_result.get('risk_attribution_id')
        if rule_result.get('risk_attribution_id') is not None else (
            rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('risk_attribution_id')
            if rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('risk_attribution_id') is not None else
            rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('riskAttributionId')
        )
    ),
    # 新增：存 risk_attribution_name，兼容两种key
    'risk_attribution_name': (
        rule_result.get('risk_attribution_name')
        if rule_result.get('risk_attribution_name') is not None else (
            rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('risk_attribution_name')
            if rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('risk_attribution_name') is not None else
            rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('riskAttributionName')
        )
    ),
}
```

### 6. 前端返回数据

在返回给前端的数据中，同时包含 snake_case 和 camelCase 版本：

```python
"list": [
    {
        "result": 1,
        "riskLevel": 2,
        "ruleName": "付款条款审查",
        "ruleId": 1,
        # 新增风险归属信息
        "riskAttributionId": 101,
        "riskAttributionName": "财务部",
        "review_result": "FAIL",
        # ... 其他字段
    }
]
```

## 数据库表结构

`confirm_review_rule_result` 表包含以下字段：

```sql
-- 风险归属ID字段
`risk_attribution_id` INT NULL COMMENT '风险归属ID'

-- 风险归属名字段  
`risk_attribution_name` VARCHAR(255) NULL COMMENT '风险归属名'
```

## 数据库迁移

执行以下 SQL 脚本添加字段：

```sql
-- 添加风险归属ID字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `risk_attribution_id` INT NULL COMMENT '风险归属ID' 
AFTER `contract_name`;

-- 添加风险归属名字段
ALTER TABLE `confirm_review_rule_result` 
ADD COLUMN `risk_attribution_name` VARCHAR(255) NULL COMMENT '风险归属名' 
AFTER `risk_attribution_id`;
```

## 测试建议

1. **前端测试**：确保前端正确传递 `riskAttributionId` 和 `riskAttributionName` 字段
2. **API测试**：使用 Postman 或 curl 测试 `/chat/confirm` 接口
3. **数据库验证**：检查 `confirm_review_rule_result` 表中是否正确保存了风险归属信息
4. **返回数据验证**：确认前端收到的响应中包含正确的风险归属字段

## 注意事项

1. 字段值优先级：LLM输出 > 前端传入 > 默认值
2. 命名兼容性：同时支持 camelCase 和 snake_case
3. 数据库约束：字段可为空，适应不同场景
4. 前端兼容：返回数据同时包含两种命名风格 