# 现有审查记录CRUD接口文档

## 概述

系统已经存在完整的审查记录CRUD接口，位于 `/api/contract-audit-reviews` 路径下。这些接口提供了对保存的审查数据进行完整的增删改查操作。

## 数据库模型

### ContractAuditReview 模型

```python
class ContractAuditReview(Base):
    __tablename__ = 'contract_audit_review'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_name = Column(Text, nullable=False)  # 审查项目名称
    risk_level = Column(Enum('高', '中', '低', '无'), default='无')  # 风险等级
    review_status = Column(Enum('通过', '不通过', '待审查'), default='待审查')  # 审查状态
    reviewer = Column(Text, nullable=True)  # 审查人
    review_comment = Column(Text, nullable=True)  # 审查备注
    is_deleted = Column(Boolean, default=False)  # 是否删除
    ext_json = Column(JSON, nullable=True)  # 扩展字段（存储结构化审查结果）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## API接口列表

### 1. 创建审查记录

**接口**: `POST /api/contract-audit-reviews`

**功能**: 创建新的审查记录

**请求体**:
```json
{
  "project_name": "合同审查项目",
  "risk_level": "中",
  "review_status": "不通过",
  "reviewer": "AI助手",
  "review_comment": "审查总结",
  "ext_json": {
    "structured_result": {...},
    "session_id": "session_123",
    "user_id": "user_123"
  }
}
```

**响应**:
```json
{
  "id": 1,
  "project_name": "合同审查项目",
  "risk_level": "中",
  "review_status": "不通过",
  "reviewer": "AI助手",
  "review_comment": "审查总结",
  "ext_json": {...},
  "is_deleted": false,
  "updated_at": "2024-01-01T12:00:00",
  "created_at": "2024-01-01T12:00:00"
}
```

### 2. 获取单个审查记录

**接口**: `GET /api/contract-audit-reviews/{review_id}`

**功能**: 根据ID获取审查记录详情

**响应**: 返回单个审查记录对象

### 3. 获取审查记录列表

**接口**: `GET /api/contract-audit-reviews`

**功能**: 获取所有审查记录

**查询参数**:
- `skip`: 跳过记录数（默认0）
- `limit`: 返回记录数（默认100，最大1000）

**响应**: 返回审查记录列表

### 4. 更新审查记录

**接口**: `PUT /api/contract-audit-reviews/{review_id}`

**功能**: 更新指定的审查记录

**请求体**:
```json
{
  "project_name": "更新后的项目名称",
  "risk_level": "高",
  "review_status": "通过",
  "reviewer": "更新后的审查人",
  "review_comment": "更新后的备注"
}
```

**响应**: 返回更新后的审查记录

### 5. 删除审查记录

**接口**: `DELETE /api/contract-audit-reviews/{review_id}`

**功能**: 软删除指定的审查记录

**响应**:
```json
{
  "message": "Review deleted"
}
```

### 6. 分页查询审查记录（增强版）

**接口**: `GET /api/contract-audit-reviews/page`

**功能**: 分页获取审查记录，支持多种过滤条件

**查询参数**:
- `page`: 页码（从1开始）
- `page_size`: 每页数量（1-100）
- `session_id`: 会话ID过滤（可选）
- `risk_level`: 风险等级过滤（可选）
- `review_status`: 审查状态过滤（可选）

**响应**:
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "project_name": "合同审查项目",
      "risk_level": "中",
      "review_status": "不通过",
      "reviewer": "AI助手",
      "review_comment": "审查总结",
      "ext_json": {...},
      "is_deleted": false,
      "updated_at": "2024-01-01T12:00:00",
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### 7. 根据会话ID获取审查记录

**接口**: `GET /api/contract-audit-reviews/by-session/{session_id}`

**功能**: 获取指定会话的所有审查记录

**响应**: 返回该会话的所有审查记录列表

### 8. 获取审查记录统计信息

**接口**: `GET /api/contract-audit-reviews/stats`

**功能**: 获取审查记录的统计信息

**查询参数**:
- `session_id`: 会话ID（可选，用于过滤特定会话的统计）

**响应**:
```json
{
  "total_count": 100,
  "risk_level_stats": {
    "高": 20,
    "中": 30,
    "低": 40,
    "无": 10
  },
  "review_status_stats": {
    "通过": 60,
    "不通过": 35,
    "待审查": 5
  },
  "summary": {
    "high_risk_count": 20,
    "medium_risk_count": 30,
    "low_risk_count": 40,
    "passed_count": 60,
    "failed_count": 35
  }
}
```

## 使用示例

### 1. 创建审查记录

```bash
curl -X POST "http://localhost:8001/api/contract-audit-reviews" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "合同审查项目A",
    "risk_level": "中",
    "review_status": "不通过",
    "reviewer": "AI助手",
    "review_comment": "发现3个风险点",
    "ext_json": {
      "structured_result": {
        "contract_name": "测试合同",
        "overall_risk_level": "medium",
        "total_issues": 3
      },
      "session_id": "session_123",
      "user_id": "user_123"
    }
  }'
```

### 2. 分页查询带过滤

```bash
curl "http://localhost:8001/api/contract-audit-reviews/page?page=1&page_size=10&session_id=session_123&risk_level=中"
```

### 3. 获取会话的审查记录

```bash
curl "http://localhost:8001/api/contract-audit-reviews/by-session/session_123"
```

### 4. 获取统计信息

```bash
curl "http://localhost:8001/api/contract-audit-reviews/stats?session_id=session_123"
```

## 与新增接口的对比

| 功能 | 现有接口 | 新增接口 | 说明 |
|------|----------|----------|------|
| 创建记录 | `POST /api/contract-audit-reviews` | `POST /chat/save-review` | 现有接口更通用，新接口专门用于保存审查结果 |
| 按ID查询 | `GET /api/contract-audit-reviews/{id}` | ❌ | 现有接口功能 |
| 按session查询 | `GET /api/contract-audit-reviews/by-session/{session_id}` | `GET /chat/saved-reviews/{session_id}` | 功能相同 |
| 分页查询 | `GET /api/contract-audit-reviews/page` | ❌ | 现有接口功能更强大，支持多种过滤 |
| 统计信息 | `GET /api/contract-audit-reviews/stats` | ❌ | 现有接口功能 |
| 更新记录 | `PUT /api/contract-audit-reviews/{id}` | ❌ | 现有接口功能 |
| 删除记录 | `DELETE /api/contract-audit-reviews/{id}` | `DELETE /chat/saved-reviews/{review_id}` | 功能相同 |
| 批量保存 | ❌ | `POST /chat/save-multiple-reviews` | 新功能 |

## 建议使用策略

### 1. **优先使用现有接口**
- 对于通用的CRUD操作，优先使用 `/api/contract-audit-reviews` 系列接口
- 现有接口功能更完整，支持更多查询条件

### 2. **使用新增接口的场景**
- 专门用于保存审查结果时，使用 `/chat/save-review`
- 需要批量保存时，使用 `/chat/save-multiple-reviews`
- 与confirm接口配合使用时，使用 `/chat/saved-reviews/{session_id}`

### 3. **接口选择指南**

**查询操作**:
- 按ID查询: `GET /api/contract-audit-reviews/{id}`
- 按session查询: `GET /api/contract-audit-reviews/by-session/{session_id}`
- 分页查询: `GET /api/contract-audit-reviews/page`
- 统计信息: `GET /api/contract-audit-reviews/stats`

**创建操作**:
- 通用创建: `POST /api/contract-audit-reviews`
- 保存审查结果: `POST /chat/save-review`
- 批量保存: `POST /chat/save-multiple-reviews`

**更新操作**:
- 更新记录: `PUT /api/contract-audit-reviews/{id}`

**删除操作**:
- 删除记录: `DELETE /api/contract-audit-reviews/{id}` 或 `DELETE /chat/saved-reviews/{review_id}`

## 总结

系统已经提供了完整的审查记录CRUD功能，包括：

✅ **现有完整功能**:
- 创建、查询、更新、删除审查记录
- 分页查询支持多种过滤条件
- 按会话ID查询
- 统计信息查询
- 软删除支持

✅ **新增补充功能**:
- 专门用于保存审查结果的接口
- 批量保存功能
- 与confirm接口的集成

建议根据具体使用场景选择合适的接口，现有接口已经能够满足大部分需求。 