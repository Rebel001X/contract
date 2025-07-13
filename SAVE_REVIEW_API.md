# 保存审查结果API文档

## 概述

本文档描述了合同审计系统中保存审查结果到MySQL数据库的API接口。系统采用方案2（职责分离），将审查功能和数据持久化功能分离，提供更好的性能和用户体验。

## 数据库配置

### MySQL数据库连接

在 `.env` 文件中配置MySQL数据库连接：

```env
# MySQL数据库配置
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/contract_audit?charset=utf8mb4
```

### 数据库表结构

确保MySQL数据库中已创建 `contract_audit_review` 表：

```sql
CREATE TABLE `contract_audit_review` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_name` text NOT NULL COMMENT '审查项目（长文本）',
  `risk_level` enum('高','中','低','无') NOT NULL DEFAULT '无' COMMENT '风险等级',
  `review_status` enum('通过','不通过','待审查') NOT NULL DEFAULT '待审查' COMMENT '审查状态',
  `reviewer` text COMMENT '审查人（长文本）',
  `review_comment` text COMMENT '审查备注/说明（长文本）',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否删除 0-正常 1-已删除',
  `ext_json` json DEFAULT NULL COMMENT '扩展字段（可存储额外信息）',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_risk_level` (`risk_level`),
  KEY `idx_review_status` (`review_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同审计-审查记录表';
```

## API接口

### 1. 保存单个审查结果

**接口路径**: `POST /chat/save-review`

**功能描述**: 将结构化审查结果保存到数据库

**请求参数**:

```json
{
  "session_id": "session_123",
  "structured_result": {
    "contract_name": "合同名称",
    "overall_risk_level": "medium",
    "total_issues": 3,
    "high_risk_items": 1,
    "medium_risk_items": 1,
    "low_risk_items": 1,
    "overall_summary": "审查总结",
    "critical_recommendations": ["建议1", "建议2"],
    "action_items": ["行动1", "行动2"],
    "confidence_score": 0.85
  },
  "user_id": "user_123",
  "project_name": "项目名称",
  "reviewer": "AI助手"
}
```

**响应示例**:

```json
{
  "message": "审查结果已成功保存",
  "review_id": 1,
  "session_id": "session_123",
  "saved_at": "2024-01-01T12:00:00"
}
```

### 2. 批量保存审查结果

**接口路径**: `POST /chat/save-multiple-reviews`

**功能描述**: 批量保存多个审查结果到数据库

**请求参数**:

```json
{
  "reviews": [
    {
      "session_id": "session_123",
      "structured_result": {
        "contract_name": "合同1",
        "overall_risk_level": "medium",
        "total_issues": 2,
        "overall_summary": "审查总结1"
      },
      "project_name": "项目1",
      "reviewer": "AI助手"
    },
    {
      "session_id": "session_124",
      "structured_result": {
        "contract_name": "合同2",
        "overall_risk_level": "low",
        "total_issues": 1,
        "overall_summary": "审查总结2"
      },
      "project_name": "项目2",
      "reviewer": "AI助手"
    }
  ],
  "user_id": "user_123"
}
```

**响应示例**:

```json
{
  "message": "成功保存 2 个审查结果",
  "saved_count": 2,
  "review_ids": [1, 2]
}
```

### 3. 获取保存的审查结果

**接口路径**: `GET /chat/saved-reviews/{session_id}`

**功能描述**: 获取指定会话的已保存审查结果

**响应示例**:

```json
{
  "session_id": "session_123",
  "total_count": 2,
  "reviews": [
    {
      "id": 1,
      "project_name": "合同审查 - session_123",
      "risk_level": "中",
      "review_status": "不通过",
      "reviewer": "AI助手",
      "review_comment": "审查总结",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00",
      "ext_json": {
        "structured_result": {...},
        "session_id": "session_123",
        "user_id": "user_123",
        "review_timestamp": "2024-01-01T12:00:00"
      }
    }
  ]
}
```

### 4. 删除审查记录

**接口路径**: `DELETE /chat/saved-reviews/{review_id}`

**功能描述**: 删除指定的审查记录（软删除）

**响应示例**:

```json
{
  "message": "审查记录已删除",
  "review_id": 1
}
```

## 前端集成示例

### 1. 调用confirm接口并处理保存提示

```javascript
// 调用confirm接口
const response = await fetch('/chat/confirm', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        session_id: sessionId,
        message: message,
        auto_save: true,
        user_id: userId,
        project_name: projectName
    })
});

// 处理流式响应
const reader = response.body.getReader();
while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const event = JSON.parse(new TextDecoder().decode(value));
    
    if (event.event === 'save_available') {
        // 收到保存提示，可以选择自动保存或手动保存
        const saveData = event.data;
        
        if (saveData.auto_save) {
            // 自动保存
            await saveReviewResult(saveData);
        } else {
            // 显示保存按钮，让用户手动保存
            showSaveButton(saveData);
        }
    }
}

// 保存函数
async function saveReviewResult(saveData) {
    try {
        const response = await fetch('/chat/save-review', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: saveData.session_id,
                structured_result: saveData.structured_result,
                user_id: saveData.user_id,
                project_name: saveData.project_name,
                reviewer: 'AI助手'
            })
        });
        
        const result = await response.json();
        console.log('保存成功:', result);
        
        // 显示成功消息
        showSuccessMessage('审查结果已保存');
        
    } catch (error) {
        console.error('保存失败:', error);
        showErrorMessage('保存失败，请重试');
    }
}
```

### 2. 获取保存的审查结果

```javascript
async function getSavedReviews(sessionId) {
    try {
        const response = await fetch(`/chat/saved-reviews/${sessionId}`);
        const result = await response.json();
        
        console.log('获取到的审查结果:', result);
        
        // 显示审查结果列表
        displayReviewList(result.reviews);
        
    } catch (error) {
        console.error('获取失败:', error);
    }
}
```

### 3. 删除审查记录

```javascript
async function deleteReview(reviewId) {
    try {
        const response = await fetch(`/chat/saved-reviews/${reviewId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        console.log('删除成功:', result);
        
        // 刷新列表
        await getSavedReviews(sessionId);
        
    } catch (error) {
        console.error('删除失败:', error);
    }
}
```

## 数据映射规则

### 风险等级映射

| 英文 | 中文 |
|------|------|
| high | 高 |
| medium | 中 |
| low | 低 |
| none | 无 |

### 审查状态判断

- **通过**: `total_issues == 0`
- **不通过**: `total_issues > 0`

## 错误处理

### 常见错误码

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

## 性能优化建议

1. **批量操作**: 对于多个审查结果，使用批量保存接口
2. **异步处理**: 前端可以异步处理保存操作，不阻塞用户界面
3. **缓存策略**: 对于频繁查询的审查结果，可以考虑添加缓存
4. **分页查询**: 对于大量数据，建议添加分页功能

## 测试

运行测试脚本验证功能：

```bash
python test_save_review.py
```

测试脚本会验证：
- 保存单个审查结果
- 获取保存的审查结果
- 删除审查记录
- confirm接口的保存提示功能 