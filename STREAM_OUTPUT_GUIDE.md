# 流式输出功能使用指南

## 概述

ContractAudit 系统的流式输出功能已经升级，现在支持结构化的事件数据输出，而不仅仅是纯文本内容。

## 新功能特性

### 1. 结构化事件输出

流式输出现在包含以下事件类型：

- **start**: 开始处理请求
- **context_ready**: 上下文检索完成
- **token**: 每个token的输出
- **complete**: 输出完成
- **error**: 错误事件

### 2. 事件数据结构

每个事件都包含以下字段：

```json
{
  "event": "事件类型",
  "timestamp": 时间戳,
  "data": {
    // 事件特定的数据
  }
}
```

### 3. 具体事件格式

#### start 事件
```json
{
  "event": "start",
  "timestamp": 1703123456.789,
  "data": {
    "question": "用户问题",
    "status": "processing"
  }
}
```

#### context_ready 事件
```json
{
  "event": "context_ready",
  "timestamp": 1703123457.123,
  "data": {
    "context_length": 1500,
    "prompt_length": 200
  }
}
```

#### token 事件
```json
{
  "event": "token",
  "timestamp": 1703123458.456,
  "data": {
    "content": "token内容",
    "token_index": 1,
    "is_final": false
  }
}
```

#### complete 事件
```json
{
  "event": "complete",
  "timestamp": 1703123460.789,
  "data": {
    "total_tokens": 150,
    "status": "success"
  }
}
```

#### error 事件
```json
{
  "event": "error",
  "timestamp": 1703123461.012,
  "data": {
    "error": "错误信息",
    "error_type": "错误类型",
    "error_code": "错误代码",
    "status": "failed",
    "timestamp": 1703123461.012,
    "rule_confirm_info": {
      "url": "rule/confirm接口URL",
      "contract_id": "合同ID",
      "censored_rules_count": 2,
      "censored_rule_ids": [6, 8],
      "rule_id": "规则ID（兜底处理时）",
      "fallback_reason": "兜底处理原因（兜底处理时）",
      "fallback_result": "兜底处理结果（兜底处理时）",
      "response_status": 200,
      "response_length": 1234,
      "business_error_code": 14000000,
      "business_error_message": "业务错误信息",
      "unknown_error_code": 99999999,
      "response_message": "响应消息",
      "response_type": "响应类型",
      "response_value": "响应值"
    }
  }
}
```

**错误类型说明：**
- `error_type`: 错误类型分类（如：请求超时、网络连接失败、JSON解析失败、业务逻辑失败等）
- `error_code`: 错误代码标识（如：RULE_CONFIRM_TIMEOUT、RULE_CONFIRM_CONNECTION_FAILED等）
- `rule_confirm_info`: rule/confirm相关的详细信息（仅在rule/confirm相关错误时包含）

## 使用方法

### 1. API 调用

流式输出端点：`POST /chat/stream`

```bash
curl -X POST "http://localhost:8001/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "message": "请分析这个合同的风险点"
  }'
```

### 2. JavaScript 客户端

```javascript
fetch('/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    session_id: 'your_session_id',
    message: '请分析这个合同的风险点'
  })
})
.then(response => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  function readStream() {
    return reader.read().then(({ done, value }) => {
      if (done) return;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // 保留不完整的行
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const eventData = JSON.parse(line.substring(6));
            handleEvent(eventData);
          } catch (e) {
            console.error('JSON解析错误:', e);
          }
        }
      }
      
      return readStream();
    });
  }
  
  return readStream();
});

function handleEvent(eventData) {
  switch (eventData.event) {
    case 'start':
      console.log('开始处理:', eventData.data.question);
      break;
    case 'context_ready':
      console.log('上下文准备完成:', eventData.data);
      break;
    case 'token':
      // 累积token内容
      appendToken(eventData.data.content);
      break;
    case 'complete':
      console.log('输出完成，总token数:', eventData.data.total_tokens);
      break;
    case 'error':
      console.error('发生错误:', eventData.data.error);
      break;
  }
}
```

## 测试工具

### 1. 命令行测试

使用提供的测试脚本：

```bash
cd rag642
python test_stream.py
```

### 2. Web 界面测试

启动服务器后，访问以下URL进行测试：

- 完整测试页面：`http://localhost:8001/test/stream`
- 简单测试页面：`http://localhost:8001/test/stream-simple`

### 3. 使用 curl 测试

```bash
# 测试流式输出
curl -X POST "http://localhost:8001/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "请分析这个合同的风险点"}' \
  --no-buffer
```

## 兼容性说明

### 向后兼容

- 原有的 `/chat` 端点保持不变
- 新的流式输出格式不影响现有功能

### 前端适配

如果前端需要适配新的流式输出格式，需要：

1. 解析 JSON 格式的事件数据
2. 根据事件类型进行不同处理
3. 累积 token 内容以显示完整回复

### 错误处理

- 网络错误会触发 error 事件
- 解析错误会在客户端控制台显示
- 服务器错误会返回相应的 HTTP 状态码

## 性能优化建议

1. **客户端缓冲**：合理设置客户端缓冲区大小
2. **事件处理**：避免在 token 事件中进行复杂处理
3. **错误重试**：实现适当的错误重试机制
4. **连接管理**：及时关闭不需要的连接

## 故障排除

### 常见问题

1. **JSON 解析错误**
   - 检查数据格式是否正确
   - 确保使用 UTF-8 编码

2. **连接中断**
   - 检查网络连接
   - 验证服务器状态

3. **事件丢失**
   - 检查客户端缓冲区设置
   - 验证事件处理逻辑

### 调试技巧

1. 使用浏览器开发者工具查看网络请求
2. 在客户端添加详细的日志输出
3. 使用提供的测试工具验证功能

## 更新日志

- **v1.0.0**: 初始版本，支持基本流式输出
- **v1.1.0**: 升级为结构化事件输出，增加更多元数据 