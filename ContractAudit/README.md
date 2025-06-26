# ContractAudit 聊天系统

基于LangChain框架的智能合同审计对话系统，提供专业的合同分析、风险识别和法律建议功能。

## 功能特性

### 🤖 智能对话
- 基于LangChain的对话链管理
- 支持上下文记忆的连续对话
- 专业的合同审计助手角色

### 📄 文档处理
- 支持DOC/DOCX格式合同文档
- 智能文档分块和向量化
- 基于语义的相似内容检索

### 🔍 专业分析
- 合同风险分析
- 条款详细解读
- 法律合规检查
- 谈判建议生成

### 💾 会话管理
- 多用户会话支持
- 聊天历史记录
- 会话状态持久化

## 技术架构

```
ContractAudit/
├── chat.py              # 核心聊天管理器
├── main.py              # FastAPI应用入口
├── prompt template.py   # 提示词模板集合
└── __init__.py          # 模块初始化
```

### 核心组件

1. **ContractChatManager**: 聊天管理器
   - 会话创建和管理
   - 消息处理和回复生成
   - 向量存储集成

2. **LangChain集成**:
   - 文档加载器 (Docx2txtLoader)
   - 文本分割器 (RecursiveCharacterTextSplitter)
   - 向量存储 (Milvus)
   - 嵌入模型 (HuggingFaceEmbeddings)

3. **提示模板系统**:
   - 基础对话模板
   - 风险分析模板
   - 条款分析模板
   - 法律建议模板

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境配置

确保以下服务可用：
- Milvus向量数据库 (localhost:19530)
- 火山引擎Ark LLM服务

### 3. 启动服务

```bash
# 启动ContractAudit聊天服务
python -m ContractAudit.main

# 或者直接运行
cd ContractAudit
python main.py
```

服务将在 `http://localhost:8001` 启动

## API接口

### 会话管理

#### 创建会话
```http
POST /sessions
Content-Type: application/json

{
    "user_id": "user123",
    "contract_file": "contract.docx"
}
```

#### 获取会话列表
```http
GET /sessions?user_id=user123
```

#### 获取会话详情
```http
GET /sessions/{session_id}
```

#### 删除会话
```http
DELETE /sessions/{session_id}
```

### 聊天功能

#### 发送消息
```http
POST /chat
Content-Type: application/json

{
    "session_id": "session123",
    "message": "这份合同的风险点有哪些？"
}
```

#### 加载合同文档
```http
POST /sessions/{session_id}/load-contract
Content-Type: application/json

{
    "session_id": "session123",
    "contract_file": "contract.docx"
}
```

### 系统状态

#### 健康检查
```http
GET /health
```

## 使用示例

### 1. 基础对话流程

```python
from ContractAudit.chat import chat_manager

# 创建会话
session_id = chat_manager.create_session("user123", "contract.docx")

# 加载合同文档
chat_manager.load_contract_to_vectorstore("contract.docx")

# 发送消息
response = chat_manager.chat(session_id, "这份合同的主要条款是什么？")
print(response["response"])
```

### 2. 风险分析

```python
# 发送风险分析请求
response = chat_manager.chat(session_id, "请分析这份合同的风险点")
print(response["response"])
```

### 3. 条款分析

```python
# 分析特定条款
response = chat_manager.chat(session_id, "请详细分析违约责任条款")
print(response["response"])
```

## 提示模板类型

系统提供多种专业的提示模板：

1. **basic**: 基础对话模板
2. **risk_analysis**: 风险分析模板
3. **clause_analysis**: 条款分析模板
4. **comparison**: 合同对比模板
5. **summary**: 合同摘要模板
6. **legal_advice**: 法律建议模板
7. **negotiation**: 谈判建议模板

## 测试

### 运行测试

```bash
# 运行功能测试
python test_contract_chat.py

# 使用HTTP测试文件
# 在VS Code中打开 test_contract_chat.http 文件
# 点击 "Send Request" 按钮测试各个API
```

### 测试覆盖

- 聊天管理器基本功能
- 提示模板系统
- FastAPI端点
- 错误处理
- 会话管理

## 配置说明

### 向量数据库配置

在 `config.py` 中配置Milvus连接：

```python
MILVUS_DB_PATH = "localhost:19530"
MILVUS_COLLECTION_NAME = "contract_vectors"
MILVUS_VECTOR_DIM = 384  # 根据嵌入模型调整
```

### LLM服务配置

配置火山引擎Ark服务：

```python
ARK_API_KEY = "your_api_key"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
```

## 部署建议

### 生产环境

1. **数据库持久化**: 使用Redis或数据库存储会话数据
2. **负载均衡**: 使用Nginx进行负载均衡
3. **监控**: 集成Prometheus监控
4. **日志**: 使用结构化日志记录

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["python", "-m", "ContractAudit.main"]
```

## 故障排除

### 常见问题

1. **Milvus连接失败**
   - 检查Milvus服务是否启动
   - 验证连接参数

2. **嵌入模型加载失败**
   - 检查网络连接
   - 验证模型名称

3. **LLM服务不可用**
   - 检查API密钥
   - 验证服务端点

### 日志查看

```bash
# 查看应用日志
tail -f logs/contract_audit.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。 