# 合同审计系统 - 快速开始指南

## 系统概述

这是一个基于LangChain的智能合同审计对话系统，提供企业级的合同分析和风险评估功能。

## 快速启动

### 1. 环境准备

确保您已安装Python 3.8+和虚拟环境：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 2. 安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 可选：安装额外依赖（如果需要完整功能）
pip install -r requirements-optional.txt
```

### 3. 启动服务器

```bash
# 方式1：使用启动脚本
python start_server.py

# 方式2：直接运行模块
python -m ContractAudit.main

# 方式3：使用uvicorn
uvicorn ContractAudit.main:app --host 0.0.0.0 --port 8001
```

### 4. 验证服务

服务器启动后，访问以下地址验证：

- 根路径：http://localhost:8001/
- 健康检查：http://localhost:8001/health
- API文档：http://localhost:8001/docs

## API使用示例

### 1. 创建会话

```bash
curl -X POST http://localhost:8001/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'
```

### 2. 发送聊天消息

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "message": "请分析这个合同的风险点"
  }'
```

### 3. 加载合同文档

```bash
curl -X POST http://localhost:8001/sessions/your_session_id/load-contract \
  -H "Content-Type: application/json" \
  -d '{"contract_file": "/path/to/contract.docx"}'
```

### 4. 获取会话历史

```bash
curl http://localhost:8001/sessions/your_session_id
```

### 5. 列出所有会话

```bash
curl http://localhost:8001/sessions
```

## 功能特性

### 当前版本（简化版）
- ✅ 基础聊天功能
- ✅ 会话管理
- ✅ 模拟LLM回复
- ✅ 提示词模板
- ✅ RESTful API
- ✅ 健康检查

### 完整版本（需要额外配置）
- 🔄 真实LLM集成（火山引擎Ark）
- 🔄 向量数据库（Milvus）
- 🔄 文档处理（PDF、Word）
- 🔄 嵌入模型
- 🔄 高级日志记录
- 🔄 性能监控

## 配置说明

### 环境变量

创建 `.env` 文件（参考 `.env.example`）：

```env
# 基础配置
DEBUG=true
LOG_LEVEL=INFO

# 火山引擎配置（可选）
ARK_API_KEY=your_api_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com
ARK_TIMEOUT=30
ARK_MAX_RETRIES=3

# Milvus配置（可选）
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=contract_audit

# 嵌入模型配置
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_chat_manager.py

# 运行性能测试
pytest tests/test_performance.py
```

### 代码格式化

```bash
# 格式化代码
black ContractAudit/ tests/

# 检查代码风格
flake8 ContractAudit/ tests/

# 类型检查
mypy ContractAudit/
```

### Docker部署

```bash
# 构建镜像
docker build -t contract-audit .

# 运行容器
docker run -p 8001:8001 contract-audit

# 使用docker-compose
docker-compose up -d
```

## 故障排除

### 常见问题

1. **导入错误**
   - 确保在正确的目录下运行
   - 检查虚拟环境是否激活
   - 验证依赖包是否安装完整

2. **端口占用**
   - 检查8001端口是否被占用
   - 使用 `netstat -an | findstr :8001` 查看端口状态

3. **模块缺失**
   - 运行 `pip install -r requirements.txt`
   - 对于可选功能，运行 `pip install -r requirements-optional.txt`

4. **权限问题**
   - 确保有足够的文件读写权限
   - 检查防火墙设置

### 日志查看

系统会输出详细的日志信息，包括：
- 启动信息
- 会话创建/删除
- 聊天处理过程
- 错误信息

## 下一步

1. 配置真实的LLM服务（火山引擎Ark）
2. 设置向量数据库（Milvus）
3. 添加更多文档格式支持
4. 实现用户认证和权限管理
5. 添加监控和告警功能

## 技术支持

如有问题，请查看：
- 项目文档：`PROJECT_SUMMARY.md`
- 测试用例：`tests/` 目录
- 配置文件：`ContractAudit/config.py` 