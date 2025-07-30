# Rule/Confirm 接口格式改造说明

## 改造概述

将 `python/rule/confirm` 接口的请求体从简单的结果数组格式改造为标准格式，包含完整的规则定义信息。

## 改造前后对比

### 改造前格式
```javascript
[
  {
    "contractId": "1234",
    "ruleId": 3,
    "result": true
  },
  {
    "contractId": "1234", 
    "ruleId": 5,
    "result": false
  }
]
```

### 改造后标准格式
```javascript
{
  "contractId": "1234",
  "reviewRuleDtoList": [
    {
      "id": 3,
      "ruleName": "测试规则3",
      "type": 1,
      "riskLevel": 1,
      "riskAttributionId": 3,
      "riskAttributionName": "业务风险",
      "censoredSearchEngine": 1,
      "ruleGroupId": 2,
      "ruleGroupName": "分组071502",
      "includeRule": null,
      "logicRuleList": null,
      "exampleList": null,
      "conditionalIdentifier": "anyone",
      "conditionList": [
        {
          "conditionInfo": "{\"body\":\"合同总金额\",\"logicalSymbol\":\"等于\",\"conditionValue\":\"1000000\"}"
        }
      ],
      "reviseOpinion": "提示不通过0715",
      "creatorId": 0,
      "creatorName": "admin",
      "version": 0,
      "updateTime": "2025-07-15 09:44:39",
      "result": true
    }
  ]
}
```

## 主要改动

### 1. 请求体结构改造
- **位置**: `ContractAudit/main.py` 第 1027-1080 行
- **改动**: 从简单数组改为包含 `contractId` 和 `reviewRuleDtoList` 的对象结构

### 2. 规则DTO字段扩展
- **新增字段**: 包含完整的规则定义信息
- **保留字段**: `result` 字段用于传递审查结果
- **默认值**: 为缺失字段提供合理的默认值

### 3. 响应处理优化
- **位置**: `ContractAudit/main.py` 第 1200-1230 行
- **改动**: 适配标准格式响应，支持 `reviewRuleDtoList` 结构
- **兼容性**: 保留对旧格式响应的兼容处理

### 4. 调试日志增强
- **新增**: 详细的请求和响应日志
- **格式**: 标准化的日志输出格式
- **信息**: 包含请求体大小、规则数量等统计信息

## 字段映射说明

| 原字段 | 新字段 | 说明 | 默认值 |
|--------|--------|------|--------|
| `ruleId` | `id` | 规则ID | - |
| - | `ruleName` | 规则名称 | `规则{ruleId}` |
| - | `type` | 规则类型 | `0` |
| - | `riskLevel` | 风险等级 | `1` |
| - | `riskAttributionId` | 风险归属ID | `1` |
| - | `riskAttributionName` | 风险归属名称 | `默认风险归属` |
| - | `censoredSearchEngine` | 审查引擎标识 | `0` |
| - | `ruleGroupId` | 规则组ID | `1` |
| - | `ruleGroupName` | 规则组名称 | `默认分组` |
| - | `includeRule` | 包含规则 | `null` |
| - | `logicRuleList` | 逻辑规则列表 | `null` |
| - | `exampleList` | 示例列表 | `null` |
| - | `conditionalIdentifier` | 条件标识符 | `anyone` |
| - | `conditionList` | 条件列表 | `[]` |
| - | `reviseOpinion` | 修订意见 | `""` |
| - | `creatorId` | 创建者ID | `0` |
| - | `creatorName` | 创建者名称 | `admin` |
| - | `version` | 版本号 | `0` |
| - | `updateTime` | 更新时间 | `2025-01-01 00:00:00` |
| `result` | `result` | 审查结果 | - |

## 测试验证

### 测试脚本
- **文件**: `test_rule_confirm_format.py`
- **功能**: 验证标准格式请求和响应
- **运行**: `python test_rule_confirm_format.py`

### 测试内容
1. 标准格式请求体构建
2. 接口调用和响应处理
3. JSON解析和错误处理
4. 日志输出验证

## 兼容性说明

### 向后兼容
- 保留对旧格式响应的处理逻辑
- 支持多种响应结构解析
- 错误处理机制完善

### 向前兼容
- 支持标准格式的完整规则定义
- 可扩展新的规则字段
- 响应处理支持多种格式

## 部署注意事项

1. **接口地址**: 确保 `http://172.18.53.39/agent/python/rule/confirm` 可访问
2. **超时设置**: 请求超时时间设置为 30 秒
3. **错误处理**: 完善异常捕获和日志记录
4. **测试验证**: 部署前运行测试脚本验证功能

## 日志输出示例

```
================================================================================
🚀 RULE/CONFIRM API 标准格式请求详情
================================================================================
📡 URL: http://172.18.53.39/agent/python/rule/confirm
📋 请求方法: POST
⏱️  超时时间: 30秒
--------------------------------------------------------------------------------
📦 标准格式请求体 (JSON):
{
  "contractId": "1234",
  "reviewRuleDtoList": [
    {
      "id": 3,
      "ruleName": "测试规则3",
      "result": true
    }
  ]
}
--------------------------------------------------------------------------------
📊 请求体大小: 156 字符
🔢 reviewRuleDtoList 数量: 1
🆔 contractId: 1234
================================================================================
```

## 总结

本次改造成功将 `rule/confirm` 接口升级为标准格式，提供了更完整的规则定义信息，同时保持了良好的兼容性和可扩展性。改造后的接口能够更好地支持复杂的规则审查场景。 