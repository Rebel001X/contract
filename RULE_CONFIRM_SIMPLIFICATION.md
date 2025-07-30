# Rule/Confirm 调用条件简化说明

## 简化概述

将 `rule/confirm` 接口的调用条件从三个条件简化为两个条件，不再依赖 `contract_view` 接口返回的 `rules` 变量。

## 简化前后对比

### 简化前调用条件
```python
if contract_id and rules and need_rule_confirm:
    # 调用 rule/confirm 接口
```

### 简化后调用条件
```python
if contract_id and need_rule_confirm:
    # 调用 rule/confirm 接口
```

## 主要改动

### 1. 调用条件简化
- **移除依赖**: 不再依赖 `contract_view` 接口返回的 `rules` 变量
- **保留条件**: 只需要 `contract_id` 和 `need_rule_confirm=True`
- **逻辑简化**: 减少了对外部接口的依赖

### 2. 请求体构建逻辑调整
- **数据源变更**: 从使用 `contract_view` 返回的 `rules` 改为使用前端传入的 `censored_rules`
- **规则处理**: 直接使用前端传入的原始规则数据
- **结果设置**: 默认设置 `result: True`，因为这是前端传入的原始规则

### 3. 调试日志更新
- **移除规则数量**: 不再显示 `rules` 数量
- **保留关键信息**: 保留 `contract_id`、`need_rule_confirm`、`censored_rules` 数量

## 调用条件详解

### 必要条件
1. **`contract_id` 存在**: 合同ID必须存在
2. **`need_rule_confirm=True`**: 前端规则中有 `censoredSearchEngine=1` 的规则

### 触发方式
1. **自动触发**: 前端规则中有 `censoredSearchEngine=1` 的规则
2. **强制触发**: 前端传入 `force_rule_confirm: true`

## 递归查找功能

### 查找范围
- **顶层字段**: 直接在规则对象中查找
- **嵌套对象**: 在任意深度的嵌套对象中查找
- **数组元素**: 在数组/列表的每个元素中查找

### 查找路径
```javascript
// 示例：在不同位置查找 censoredSearchEngine
{
  "id": 1,
  "censoredSearchEngine": 1,           // 路径: ""
  "config": {
    "censoredSearchEngine": 1           // 路径: "config"
  },
  "subRules": [
    {
      "censoredSearchEngine": 1         // 路径: "subRules[0]"
    }
  ]
}
```

## 测试验证

### 测试脚本
- **`test_simplified_rule_confirm.py`**: 测试简化后的调用逻辑
- **`debug_rule_confirm.py`**: 调试调用条件
- **`test_recursive_censored_search.py`**: 测试递归查找功能

### 测试用例
1. **正常调用**: 有 `censoredSearchEngine=1` 的规则
2. **强制调用**: 使用 `force_rule_confirm: true`
3. **嵌套查找**: `censoredSearchEngine` 在嵌套对象中
4. **无触发条件**: 没有 `censoredSearchEngine=1` 的规则
5. **缺少合同ID**: 没有 `contractId` 字段

## 优势

### 1. 减少依赖
- 不再依赖 `contract_view` 接口的响应
- 降低了系统间的耦合度

### 2. 提高可靠性
- 减少了可能的失败点
- 简化了调用逻辑

### 3. 增强灵活性
- 支持递归查找 `censoredSearchEngine` 字段
- 支持强制调用选项

### 4. 改善调试
- 更清晰的调试日志
- 更准确的路径追踪

## 部署注意事项

1. **兼容性**: 保持对现有前端数据的兼容性
2. **测试验证**: 部署前运行测试脚本验证功能
3. **日志监控**: 关注调试日志中的调用条件检查
4. **错误处理**: 确保异常情况下的错误处理

## 总结

通过这次简化，`rule/confirm` 接口的调用变得更加简单和可靠：

- ✅ **减少依赖**: 不再依赖外部接口的 `rules` 变量
- ✅ **增强查找**: 支持递归查找 `censoredSearchEngine` 字段
- ✅ **提高可靠性**: 简化了调用逻辑，减少了失败点
- ✅ **改善调试**: 更清晰的日志输出和路径追踪

现在只要前端传入的规则中有 `censoredSearchEngine=1` 的字段（无论在哪里），并且有 `contractId`，就会正确调用 `rule/confirm` 接口。 