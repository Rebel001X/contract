# 勾选审查规则保存接口文档

## 概述

本文档描述了用于保存用户勾选审查规则的API接口。这些接口允许用户从外部API获取的审查规则列表中选择特定的规则，并将其保存到本地数据库中。

## 接口列表

### 1. 异步保存勾选审查规则

**接口路径**: `POST /api/review-rules/save-selected`

**功能描述**: 异步保存用户勾选的审查规则到数据库，使用后台任务执行，不阻塞API响应。

**请求参数**:

```json
{
  "selected_rules": [
    {
      "rule_id": 1,
      "rule_name": "合同条款风险检查",
      "type": 0,
      "risk_level": 2,
      "risk_attribution_id": 1,
      "risk_attribution_name": "合同风险",
      "censored_search_engine": 0,
      "rule_group_id": 1,
      "rule_group_name": "基础规则组",
      "include_rule": "包含规则内容",
      "logic_rule_list": [
        {"step": "测试判断逻辑规则1"},
        {"step": "测试判断逻辑规则2"}
      ],
      "example_list": [
        {"contractContent": "这是合同内容示例", "judgmentResult": "0"}
      ],
      "conditional_identifier": "0",
      "condition_list": null,
      "revise_opinion": "修改建议",
      "creator_id": 1,
      "creator_name": "创建者",
      "version": 1,
      "update_time": "2024-01-01T00:00:00Z"
    }
  ],
  "user_id": "user123",
  "project_name": "合同审查项目A",
  "description": "用户手动选择的审查规则"
}
```

**字段说明**:

- `selected_rules`: 勾选的审查规则列表（必填）
  - `rule_id`: 规则ID（必填）
  - `rule_name`: 规则名称（必填）
  - `type`: 规则类型，0-预设，1-自定义（必填）
  - `risk_level`: 风险等级，0-低风险，1-中风险，2-高风险（必填）
  - `risk_attribution_id`: 风险归属id（可选）
  - `risk_attribution_name`: 风险归属名（可选）
  - `censored_search_engine`: 审查引擎，0-大模型 1-规则推理（必填）
  - `rule_group_id`: 规则分组id（可选）
  - `rule_group_name`: 规则分组名（可选）
  - `include_rule`: 包含规则（可选）
  - `logic_rule_list`: 逻辑规则列表（可选）
  - `example_list`: 例子列表（可选）
  - `conditional_identifier`: 条件判断符（可选）
  - `condition_list`: 条件列表（可选）
  - `revise_opinion`: 修改意见（可选）
  - `creator_id`: 创建者id（可选）
  - `creator_name`: 创建者姓名（可选）
  - `version`: 版本号（默认1）
  - `update_time`: 更新时间（可选）

- `user_id`: 用户ID（可选）
- `project_name`: 项目名称（可选）
- `description`: 描述信息（可选）

**响应示例**:

```json
{
  "code": 200,
  "message": "已启动后台任务保存 2 条勾选的审查规则到数据库",
  "data": {
    "selected_count": 2,
    "saved_count": 2,
    "user_id": "user123",
    "project_name": "合同审查项目A",
    "description": "用户手动选择的审查规则"
  }
}
```

### 2. 同步保存勾选审查规则

**接口路径**: `POST /api/review-rules/save-selected-sync`

**功能描述**: 同步保存用户勾选的审查规则到数据库，立即执行并返回结果。

**请求参数**: 与异步保存接口相同

**响应示例**:

```json
{
  "code": 200,
  "message": "成功保存 2 条勾选的审查规则，跳过 0 条已存在的规则",
  "data": {
    "selected_count": 2,
    "saved_count": 2,
    "skipped_count": 0,
    "user_id": "user123",
    "project_name": "合同审查项目A",
    "description": "用户手动选择的审查规则"
  }
}
```

## 使用场景

### 1. 前端用户界面

用户在前端界面中：
1. 从外部API获取审查规则列表
2. 勾选需要的规则
3. 点击保存按钮调用接口

### 2. 批量规则导入

系统管理员可以：
1. 从外部系统导出规则列表
2. 选择需要导入的规则
3. 批量保存到本地数据库

### 3. 规则定制

用户可以：
1. 基于现有规则进行定制
2. 选择基础规则作为模板
3. 保存定制后的规则

## 错误处理

### 常见错误码

- `400`: 请求参数错误
- `500`: 服务器内部错误
- `503`: 数据库连接失败

### 错误响应示例

```json
{
  "code": 400,
  "message": "没有选择任何审查规则",
  "data": {
    "saved_count": 0
  }
}
```

## 测试示例

### Python测试代码

```python
import requests
import json

def test_save_selected_rules():
    # 模拟用户勾选的审查规则数据
    selected_rules = [
        {
            "rule_id": 1,
            "rule_name": "合同条款风险检查",
            "type": 0,
            "risk_level": 2,
            "risk_attribution_id": 1,
            "risk_attribution_name": "合同风险",
            "censored_search_engine": 0,
            "rule_group_id": 1,
            "rule_group_name": "基础规则组",
            "include_rule": "包含规则内容",
            "logic_rule_list": [
                {"step": "测试判断逻辑规则1"},
                {"step": "测试判断逻辑规则2"}
            ],
            "example_list": [
                {"contractContent": "这是合同内容示例", "judgmentResult": "0"}
            ],
            "conditional_identifier": "0",
            "condition_list": None,
            "revise_opinion": "修改建议",
            "creator_id": 1,
            "creator_name": "创建者",
            "version": 1,
            "update_time": "2024-01-01T00:00:00Z"
        }
    ]
    
    request_data = {
        "selected_rules": selected_rules,
        "user_id": "user123",
        "project_name": "合同审查项目A",
        "description": "用户手动选择的审查规则"
    }
    
    # 调用异步保存接口
    response = requests.post(
        "http://localhost:8001/api/review-rules/save-selected",
        json=request_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"保存成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
    else:
        print(f"保存失败: {response.text}")

if __name__ == "__main__":
    test_save_selected_rules()
```

### cURL测试命令

```bash
# 异步保存
curl -X POST "http://localhost:8001/api/review-rules/save-selected" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_rules": [
      {
        "rule_id": 1,
        "rule_name": "合同条款风险检查",
        "type": 0,
        "risk_level": 2,
        "censored_search_engine": 0,
        "version": 1
      }
    ],
    "user_id": "user123",
    "project_name": "测试项目"
  }'

# 同步保存
curl -X POST "http://localhost:8001/api/review-rules/save-selected-sync" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_rules": [
      {
        "rule_id": 2,
        "rule_name": "付款条款审查",
        "type": 1,
        "risk_level": 1,
        "censored_search_engine": 1,
        "version": 1
      }
    ],
    "user_id": "user123",
    "project_name": "测试项目"
  }'
```

## 注意事项

1. **去重机制**: 系统会根据 `rule_id` 检查规则是否已存在，避免重复插入
2. **异步处理**: 异步保存接口使用后台任务，不会阻塞API响应
3. **数据验证**: 系统会验证必填字段，确保数据完整性
4. **错误日志**: 所有错误都会记录到系统日志中
5. **事务处理**: 同步保存接口使用数据库事务，确保数据一致性

## 相关接口

- `GET /api/review-rules` - 获取已保存的审查规则
- `GET /api/review-rules/count` - 获取审查规则总数
- `POST /api/external/review-rules` - 获取外部审查规则列表 