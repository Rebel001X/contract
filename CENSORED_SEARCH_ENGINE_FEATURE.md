# CensoredSearchEngine 功能实现总结

## 功能描述

当 `censoredSearchEngine=1` 时，规则不应该传给 `contract/view` 接口，而是直接使用 `rule/confirm` 的结果。这个功能需要递归查找嵌套 JSON 中的 `censoredSearchEngine` 字段。

## 实现方案

### 1. **递归查找函数**

实现了 `find_censored_search_engine` 函数，能够递归查找嵌套 JSON 中的 `censoredSearchEngine` 字段：

```python
def find_censored_search_engine(obj, path=""):
    """递归查找 censoredSearchEngine 字段"""
    if isinstance(obj, dict):
        # 检查当前层级是否有 censoredSearchEngine 字段
        censored_search_engine = obj.get('censoredSearchEngine')
        if censored_search_engine is None:
            censored_search_engine = obj.get('censored_search_engine')
        if censored_search_engine is not None:
            return censored_search_engine, path
        
        # 递归查找子对象
        for key, value in obj.items():
            result, new_path = find_censored_search_engine(value, f"{path}.{key}" if path else key)
            if result is not None:
                return result, new_path
                
    elif isinstance(obj, list):
        # 递归查找列表中的每个元素
        for i, item in enumerate(obj):
            result, new_path = find_censored_search_engine(item, f"{path}[{i}]" if path else f"[{i}]")
            if result is not None:
                return result, new_path
    
    return None, path
```

### 2. **规则过滤逻辑**

在 `chat/confirm` 接口中，实现了规则过滤逻辑：

```python
# 过滤规则：只保留 censoredSearchEngine=0 的规则给 contract/view
frontend_rules = message_data.get('reviewRules') or message_data.get('review_rules') or []
filtered_rules = []
censored_rules = []  # 用于后续 rule/confirm 处理

for rule in frontend_rules:
    # 递归查找 censoredSearchEngine 字段
    censored_search_engine, found_path = find_censored_search_engine(rule)
    rule_id = rule.get('ruleId') or rule.get('id') or 'unknown'
    
    if censored_search_engine == 1:
        # censoredSearchEngine=1 的规则不传给 contract/view，只用于 rule/confirm
        censored_rules.append(rule)
    else:
        # censoredSearchEngine=0 或未设置的规则传给 contract/view
        filtered_rules.append(rule)
```

### 3. **contract/view 接口调用**

修改了 `contract_view_payload` 的构建逻辑，只使用过滤后的规则：

```python
# 使用过滤后的规则构建 contract_view 请求
for k in contract_view_fields:
    if k == "reviewRules":
        # 使用过滤后的规则（只包含 censoredSearchEngine=0 的规则）
        value = [dict_keys_to_camel(rule) for rule in filtered_rules]
    # ... 其他字段处理
```

### 4. **rule/confirm 处理逻辑**

修改了规则处理逻辑，使用之前过滤好的 `censored_rules` 列表：

```python
# 检查当前规则是否在 censored_rules 列表中（censoredSearchEngine=1）
current_rule_censored = fr in censored_rules

if current_rule_censored and rule_engine_result and isinstance(rule_engine_result, dict) and not rule_engine_result.get('error'):
    # 处理 rule/confirm 响应结果
    # ...
```

## 关键修复

### 1. **正确处理 censoredSearchEngine=0**

修复了 `find_censored_search_engine` 函数中的逻辑错误：

**修复前：**
```python
censored_search_engine = obj.get('censoredSearchEngine') or obj.get('censored_search_engine')
```

**修复后：**
```python
censored_search_engine = obj.get('censoredSearchEngine')
if censored_search_engine is None:
    censored_search_engine = obj.get('censored_search_engine')
```

这个修复解决了 `censoredSearchEngine=0` 被误判为 `None` 的问题。

### 2. **避免重复查找**

删除了重复的 `find_censored_search_engine` 函数定义和重复的规则检查逻辑，直接使用之前已经过滤好的 `censored_rules` 列表。

## 测试验证

创建了测试脚本 `test_simple_censored.py` 来验证功能：

1. **基本过滤逻辑测试**：验证 `censoredSearchEngine=1` 的规则被正确过滤
2. **嵌套查找测试**：验证递归查找功能在各种嵌套结构中的正确性

测试结果：
```
✅ contract/view 规则过滤正确
✅ rule/confirm 规则过滤正确
🎉 嵌套查找测试全部通过！
```

## 功能特点

1. **递归查找**：能够处理任意深度的嵌套 JSON 结构
2. **兼容性**：支持 `censoredSearchEngine` 和 `censored_search_engine` 两种字段名
3. **容错性**：对于没有 `censoredSearchEngine` 字段的规则，默认传给 `contract/view`
4. **调试友好**：添加了详细的调试日志，便于问题排查

## 使用场景

- `censoredSearchEngine=1`：规则只通过 `rule/confirm` 处理，不传给 `contract/view`
- `censoredSearchEngine=0`：规则传给 `contract/view` 处理
- 未设置 `censoredSearchEngine`：默认传给 `contract/view` 处理

这个实现确保了 `censoredSearchEngine=1` 的规则能够正确地跳过 `contract/view` 接口，直接使用 `rule/confirm` 的结果。 