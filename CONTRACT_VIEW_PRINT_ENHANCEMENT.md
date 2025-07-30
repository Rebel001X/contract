# Contract View API 打印功能增强

## 概述
为了便于调试和监控 contract_view API 的调用情况，我们在 `ContractAudit/main.py` 中添加了详细的请求和响应打印功能。

## 新增功能

### 1. 请求体详细打印
**位置**: `ContractAudit/main.py` (lines ~760-780)

```python
# 详细打印 contract_view 请求体
import json
print("=" * 80)
print("🚀 CONTRACT_VIEW API 请求详情")
print("=" * 80)
print(f"📡 URL: {url}")
print(f"📋 请求方法: POST")
print(f"⏱️  超时时间: 60秒")
print("-" * 80)
print("📦 请求体 (JSON):")
print(json.dumps(contract_view_payload, indent=2, ensure_ascii=False))
print("-" * 80)
print(f"📊 请求体大小: {len(json.dumps(contract_view_payload, ensure_ascii=False))} 字符")
print(f"🔢 reviewRules 数量: {len(contract_view_payload.get('reviewRules', []))}")
print(f"🆔 contractId: {contract_view_payload.get('contractId', 'N/A')}")
print(f"📝 reviewStage: {contract_view_payload.get('reviewStage', 'N/A')}")
print(f"📋 reviewList: {contract_view_payload.get('reviewList', 'N/A')}")
print("=" * 80)
```

### 2. 响应体详细打印
**位置**: `ContractAudit/main.py` (lines ~810-830)

```python
# 详细打印 contract_view 响应结果
print("=" * 80)
print("📥 CONTRACT_VIEW API 响应详情")
print("=" * 80)
if contract_view_result:
    if "error" in contract_view_result:
        print(f"❌ 响应状态: 错误")
        print(f"🚨 错误信息: {contract_view_result['error']}")
    else:
        print(f"✅ 响应状态: 成功")
        print(f"📊 响应体大小: {len(json.dumps(contract_view_result, ensure_ascii=False))} 字符")
        print(f"🔢 响应体键数量: {len(contract_view_result.keys())}")
        print(f"📋 响应体键列表: {list(contract_view_result.keys())}")
        print("-" * 80)
        print("📦 响应体 (JSON):")
        print(json.dumps(contract_view_result, indent=2, ensure_ascii=False))
else:
    print("❌ 响应状态: 无响应")
print("=" * 80)
```

### 3. 规则提取详细打印
**位置**: `ContractAudit/main.py` (lines ~840-870)

```python
print("=" * 80)
print("🔍 规则提取详情")
print("=" * 80)
print(f"📊 contract_view_result 类型: {type(contract_view_result)}")
print(f"📋 contract_view_result 键: {list(contract_view_result.keys()) if isinstance(contract_view_result, dict) else 'N/A'}")

rules = extract_rules(contract_view_result)
print(f"🔢 方法1提取规则数量: {len(rules)}")

if not rules:
    rules = extract_rules_from_numbered_dict(contract_view_result)
    print(f"🔢 方法2提取规则数量: {len(rules)}")

# 新增递归提取，合并所有 result_list
all_result_list_rules = extract_all_result_lists(contract_view_result)
print(f"🔢 递归提取规则数量: {len(all_result_list_rules)}")

if all_result_list_rules:
    # 合并去重（以 rule_id 为主）
    exist_rule_ids = set(str(r.get('rule_id')) for r in rules)
    for r in all_result_list_rules:
        if str(r.get('rule_id')) not in exist_rule_ids:
            rules.append(r)

print(f"🔢 最终合并规则数量: {len(rules)}")
if rules:
    print("📋 规则ID列表:")
    for i, rule in enumerate(rules[:5]):  # 只显示前5个
        rule_id = rule.get('rule_id') or rule.get('id') or rule.get('ruleId')
        rule_name = rule.get('rule_name') or rule.get('ruleName') or 'N/A'
        print(f"  {i+1}. ID: {rule_id}, 名称: {rule_name}")
    if len(rules) > 5:
        print(f"  ... 还有 {len(rules) - 5} 个规则")
print("=" * 80)
```

## 输出示例

### 请求体打印示例
```
================================================================================
🚀 CONTRACT_VIEW API 请求详情
================================================================================
📡 URL: http://172.20.228.63:8888/api/v1/query/contract_view
📋 请求方法: POST
⏱️  超时时间: 60秒
--------------------------------------------------------------------------------
📦 请求体 (JSON):
{
  "reviewStage": "初审",
  "reviewList": 2,
  "reviewRules": [
    {
      "id": 1,
      "ruleName": "不得空白签字",
      "type": 0,
      "riskLevel": 2,
      "riskAttributionId": 101,
      "riskAttributionName": "法律部",
      "censoredSearchEngine": 0,
      "ruleGroupId": 10,
      "ruleGroupName": "签署规范",
      "includeRule": "签字页必须填写",
      "exampleList": [
        {
          "contractContent": "string",
          "judgmentResult": "string"
        }
      ],
      "conditionalIdentifier": "",
      "resultList": []
    }
  ],
  "contractId": "8888"
}
--------------------------------------------------------------------------------
📊 请求体大小: 1234 字符
🔢 reviewRules 数量: 1
🆔 contractId: 8888
📝 reviewStage: 初审
📋 reviewList: 2
================================================================================
```

### 响应体打印示例
```
================================================================================
📥 CONTRACT_VIEW API 响应详情
================================================================================
✅ 响应状态: 成功
📊 响应体大小: 5678 字符
🔢 响应体键数量: 5
📋 响应体键列表: ['contractId', 'reviewRules', 'status', 'message', 'data']
--------------------------------------------------------------------------------
📦 响应体 (JSON):
{
  "contractId": "8888",
  "reviewRules": [...],
  "status": "success",
  "message": "审查完成",
  "data": {...}
}
================================================================================
```

## 日志记录
所有打印信息也会同时记录到日志文件中：
- `log_debug()` 函数会将信息写入 `confirm_debug.log` 文件
- 便于后续分析和调试

## 测试脚本
创建了 `test_contract_view_print.py` 来测试打印功能，可以独立运行验证格式是否正确。

## 优势
1. **详细的信息展示**: 包含请求/响应的完整信息
2. **格式化的输出**: 使用 JSON 格式化，便于阅读
3. **统计信息**: 显示请求体大小、规则数量等关键指标
4. **错误处理**: 区分成功和错误状态
5. **日志记录**: 同时记录到文件，便于追踪 