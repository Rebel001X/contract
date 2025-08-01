# Rule/Confirm 接口返回数据格式说明

## 概述

`rule/confirm` 接口返回的数据经过整合后，会以特定的格式返回给前端。本文档详细说明了数据整合的流程和最终的数据格式。

## 数据整合流程

### 1. **Rule/Confirm 原始响应**

`rule/confirm` 接口返回的原始数据格式：
```json
{
  "code": 10000000,
  "data": false,
  "message": "规则检查未通过"
}
```

或者：
```json
{
  "code": 10000000,
  "data": true,
  "message": "规则检查通过"
}
```

### 2. **响应解析逻辑**

系统会解析 `rule/confirm` 响应中的布尔值：

```python
# 修复：更清晰的响应解析逻辑
if 'data' in rule_engine_result:
    # 直接使用 data 字段的布尔值
    rule_confirm_success = bool(rule_engine_result['data'])
elif isinstance(rule_engine_result.get('success'), bool):
    # 尝试使用 success 字段
    rule_confirm_success = rule_engine_result.get('success')
elif isinstance(rule_engine_result.get('result'), bool):
    # 尝试使用 result 字段
    rule_confirm_success = rule_engine_result.get('result')
else:
    # 默认处理：如果响应中没有明确的布尔值，根据响应内容判断
    response_text = str(rule_engine_result).lower()
    if 'true' in response_text or 'pass' in response_text or 'success' in response_text:
        rule_confirm_success = True
    elif 'false' in response_text or 'fail' in response_text or 'error' in response_text:
        rule_confirm_success = False
    else:
        # 如果无法确定，默认设为 False（保守策略）
        rule_confirm_success = False
```

### 3. **结果映射**

根据布尔值设置 `review_result`：
- `true` → `"pass"` (通过)
- `false` → `"done"` (不通过)

```python
if rule_confirm_success:
    completed_rule['review_result'] = "pass"
    completed_rule['rule_confirm_result'] = True
else:
    completed_rule['review_result'] = "done"
    completed_rule['rule_confirm_result'] = False
```

## 最终返回给前端的数据格式

### 1. **单个规则的数据格式**

每个规则经过 `process_rule_for_frontend` 处理后，会包含以下字段：

```json
{
  "ruleId": 1,
  "ruleName": "不得空白签字",
  "type": 0,
  "riskLevel": 2,
  "riskAttributionId": 101,
  "riskAttributionName": "法律部",
  "ruleGroupId": 10,
  "ruleGroupName": "签署规范",
  "includeRule": "签字页必须填写",
  "reviewResult": "pass",  // 关键字段：rule/confirm 的结果
  "overallExplanation": "规则检查通过",
  "overallResult": "通过",
  "issues": ["问题1", "问题2"],
  "analysis": "详细分析内容",
  "resultList": [
    {
      "matched_content": "匹配的内容",
      "explanation": "解释说明",
      "risk_level": 2
    }
  ]
}
```

### 2. **完整的响应数据格式**

最终返回给前端的完整数据格式：

```json
{
  "event": "complete",
  "timestamp": 1703123456.789,
  "data": {
    "code": 0,
    "data": [
      {
        "ruleId": 1,
        "ruleName": "不得空白签字",
        "type": 0,
        "riskLevel": 2,
        "riskAttributionId": 101,
        "riskAttributionName": "法律部",
        "ruleGroupId": 10,
        "ruleGroupName": "签署规范",
        "includeRule": "签字页必须填写",
        "reviewResult": "pass",  // rule/confirm 结果
        "overallExplanation": "规则检查通过",
        "overallResult": "通过",
        "issues": ["问题1", "问题2"],
        "analysis": "详细分析内容"
      },
      {
        "ruleId": 2,
        "ruleName": "金额必须明确",
        "type": 0,
        "riskLevel": 1,
        "riskAttributionId": 102,
        "riskAttributionName": "财务部",
        "ruleGroupId": 11,
        "ruleGroupName": "财务规范",
        "includeRule": "金额必须明确",
        "reviewResult": "done",  // rule/confirm 结果
        "overallExplanation": "规则检查未通过",
        "overallResult": "不通过",
        "issues": ["金额不明确"],
        "analysis": "详细分析内容"
      }
    ],
    "maxPage": 1,
    "message": "全部规则审查完成",
    "rule_confirm_status": {
      "called": true,
      "censored_rules_count": 2,
      "censored_rule_ids": [1, 2],
      "rule_confirm_result": {
        "code": 10000000,
        "data": false,
        "message": "规则检查未通过"
      }
    }
  }
}
```

## 关键字段说明

### 1. **reviewResult 字段**

这是最重要的字段，表示 `rule/confirm` 的结果：
- `"pass"`：规则通过 `rule/confirm` 验证
- `"done"`：规则未通过 `rule/confirm` 验证

### 2. **rule_confirm_status 字段**

包含 `rule/confirm` 调用的状态信息：
- `called`：是否调用了 `rule/confirm` 接口
- `censored_rules_count`：需要审查的规则数量
- `censored_rule_ids`：需要审查的规则ID列表
- `rule_confirm_result`：`rule/confirm` 接口的原始响应

### 3. **数据优先级**

在 `determine_review_result_for_frontend` 函数中，系统会按以下优先级确定 `reviewResult`：

```python
def determine_review_result_for_frontend(rule_data):
    # 优先使用 rule/confirm 的结果
    if 'review_result' in rule_data:
        return rule_data['review_result']
    
    # 否则根据匹配内容判断
    match_content_value = rule_data.get('matchedContent') or rule_data.get('matched_content') or ""
    if not match_content_value or match_content_value.strip() == "":
        return "pass"  # 没有匹配内容，通过
    else:
        return "done"  # 有匹配内容，不通过
```

## 数据流程示例

### 场景1：Rule/Confirm 成功通过

1. **原始响应**：
```json
{
  "code": 10000000,
  "data": true,
  "message": "规则检查通过"
}
```

2. **解析结果**：
```python
rule_confirm_success = True
```

3. **最终规则数据**：
```json
{
  "ruleId": 1,
  "ruleName": "不得空白签字",
  "reviewResult": "pass",
  "rule_confirm_result": true
}
```

### 场景2：Rule/Confirm 失败

1. **原始响应**：
```json
{
  "code": 10000000,
  "data": false,
  "message": "规则检查未通过"
}
```

2. **解析结果**：
```python
rule_confirm_success = False
```

3. **最终规则数据**：
```json
{
  "ruleId": 1,
  "ruleName": "不得空白签字",
  "reviewResult": "done",
  "rule_confirm_result": false
}
```

## 前端使用建议

1. **检查 reviewResult 字段**：这是判断规则是否通过 `rule/confirm` 验证的主要依据
2. **查看 rule_confirm_status**：了解 `rule/confirm` 调用的整体状态
3. **处理不同状态**：
   - `reviewResult: "pass"`：规则通过，可以显示成功状态
   - `reviewResult: "done"`：规则未通过，需要显示失败状态
4. **错误处理**：如果 `rule_confirm_status.called` 为 `false`，说明没有调用 `rule/confirm` 接口

这样的数据格式确保了前端能够清楚地了解每个规则的 `rule/confirm` 处理结果，并进行相应的界面展示。 