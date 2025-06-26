# ContractAudit Chat System API文档

## 基本信息

- **服务地址**: http://localhost:8001
- **版本**: 1.0.0
- **描述**: 基于LangChain的合同审计对话系统

## 接口列表

### Root

- **路径**: `GET /`
- **描述**: 根路径

**响应示例**:

```json
{
  "status": "success"
}
```

---

### Create Session

- **路径**: `POST /sessions`
- **描述**: 创建新的聊天会话

**请求体**:

```json
{
  "properties": {
    "user_id": {
      "type": "string",
      "title": "User Id"
    },
    "contract_file": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Contract File"
    }
  },
  "type": "object",
  "required": [
    "user_id"
  ],
  "title": "CreateSessionRequest"
}
```

**响应示例**:

```json
{
  "status": "success"
}
```

---

### List Sessions

- **路径**: `GET /sessions`
- **描述**: 列出所有会话

**路径参数**:

- `user_id` (string | null) - 无描述

**响应示例**:

```json
{
  "status": "success"
}
```

---

### Chat

- **路径**: `POST /chat`
- **描述**: 发送聊天消息

**请求体**:

```json
{
  "properties": {
    "session_id": {
      "type": "string",
      "title": "Session Id"
    },
    "message": {
      "type": "string",
      "title": "Message"
    }
  },
  "type": "object",
  "required": [
    "session_id",
    "message"
  ],
  "title": "ChatRequest"
}
```

**响应示例**:

```json
{
  "status": "success"
}
```

---

### Load Contract

- **路径**: `POST /sessions/{session_id}/load-contract`
- **描述**: 为会话加载合同文档

**路径参数**:

- `session_id` (string) - 无描述

**请求体**:

```json
{
  "properties": {
    "session_id": {
      "type": "string",
      "title": "Session Id"
    },
    "contract_file": {
      "type": "string",
      "title": "Contract File"
    }
  },
  "type": "object",
  "required": [
    "session_id",
    "contract_file"
  ],
  "title": "LoadContractRequest"
}
```

**响应示例**:

```json
{
  "status": "success"
}
```

---

### Get Session

- **路径**: `GET /sessions/{session_id}`
- **描述**: 获取会话详情和历史

**路径参数**:

- `session_id` (string) - 无描述

**响应示例**:

```json
{
  "status": "success"
}
```

---

### Delete Session

- **路径**: `DELETE /sessions/{session_id}`
- **描述**: 删除会话

**路径参数**:

- `session_id` (string) - 无描述

**响应示例**:

```json
{
  "status": "success"
}
```

---

### Health Check

- **路径**: `GET /health`
- **描述**: 健康检查

**响应示例**:

```json
{
  "status": "success"
}
```

---

