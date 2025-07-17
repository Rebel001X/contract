"""
ContractAudit模块主入口文件
基于LangChain的合同审计对话系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contextlib import asynccontextmanager
import os
LOG_PATH = os.path.join(os.path.dirname(__file__), 'confirm_debug.log')
def log_debug(msg):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "ContractAudit"

# 自动检测并安装 pymysql
try:
    import pymysql
except ImportError:
    import subprocess
    print("pymysql 未安装，正在自动安装...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymysql"])
        import pymysql
        print("pymysql 安装成功！")
    except Exception as e:
        print(f"自动安装 pymysql 失败: {e}")
        print("请手动运行: pip install pymysql")

import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid

# 导入数据库相关模块
try:
    from ContractAudit.config import get_session
    from ContractAudit.models import ContractAuditReview, create_contract_audit_review
except ImportError:
    # 直接运行时使用绝对导入
    from config import get_session
    from models import ContractAuditReview, create_contract_audit_review

# 处理相对导入问题 - 支持直接运行和模块导入
# 添加项目根目录到Python路径


# 尝试导入外部路由
try:
    from ContractAudit.external_routes import router as external_router
    print("成功导入external_routes（包内相对导入）")
except ImportError:
    from external_routes import router as external_router
    print("成功导入external_routes（绝对导入）")

try:
    # 只导入完整版聊天管理器
    if __name__ == "__main__":
        from chat import get_chat_manager, ChatSession
    else:
        from .chat import get_chat_manager, ChatSession
    chat_manager = get_chat_manager()
    print("使用完整版聊天管理器")
except ImportError as e:
    print(f"导入错误: {e}")
    print("使用模拟聊天管理器")
    # 创建模拟的聊天管理器
    class MockChatManager:
        def __init__(self):
            self.sessions = {}  # 添加sessions属性
        
        def create_session(self, user_id, contract_file=None):
            return "mock_session_id"
        def chat(self, session_id, message):
            return {"response": "模拟回复", "session_id": session_id, "timestamp": "2024-01-01T00:00:00", "error": False}
        def get_session(self, session_id):
            return None
        def load_contract_to_vectorstore(self, contract_file):
            return True
        def get_session_history(self, session_id):
            return {"session_id": session_id, "messages": []}
        def list_sessions(self, user_id=None):
            return []
        def delete_session(self, session_id):
            return True
        def get_system_stats(self):
            return {"total_sessions": 0, "vector_store_available": False, "llm_client_available": False, "embeddings_available": False, "ark_available": False}
        def chat_stream(self, message, session_id=None):
            # 模拟流式输出
            
            response = f"这是对 '{message}' 的模拟回复。由于缺少 volcenginesdkarkruntime 包，使用模拟响应。"
            
            # 发送开始事件
            yield {
                "event": "start",
                "timestamp": time.time(),
                "data": {
                    "question": message,
                    "status": "processing",
                    "session_id": session_id,
                    "role": "assistant",
                    "extra_info": {
                        "model": "mock_model",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "is_mock": True
                    }
                }
            }
            
            # 发送上下文准备完成事件
            yield {
                "event": "context_ready",
                "timestamp": time.time(),
                "data": {
                    "context_length": 0,
                    "prompt_length": len(message),
                    "session_id": session_id,
                    "role": "assistant",
                    "status": "context_ready",
                    "extra_info": {
                        "has_context": False,
                        "is_mock": True
                    }
                }
            }
            
            # 模拟token流
            token_count = 0
            for char in response:
                token_count += 1
                yield {
                    "event": "token",
                    "timestamp": time.time(),
                    "data": {
                        "content": char,
                        "token_index": token_count,
                        "is_final": False,
                        "session_id": session_id,
                        "role": "assistant",
                        "extra_info": {
                            "chunk_id": token_count,
                            "content_length": len(char),
                            "is_mock": True
                        }
                    }
                }
            
            # 发送完成事件
            yield {
                "event": "complete",
                "timestamp": time.time(),
                "data": {
                    "total_tokens": token_count,
                    "status": "success",
                    "session_id": session_id,
                    "role": "assistant",
                    "is_final": True,
                    "extra_info": {
                        "processing_time": 0.1,
                        "final_message": "模拟流式输出完成",
                        "is_mock": True
                    }
                }
            }
    
    chat_manager = MockChatManager()

# 导入结构化审查相关模块
try:
    if __name__ == "__main__":
        from structured_models import ComprehensiveContractReview, ContractSubjectReview, PaymentClauseReview, BreachClauseReview, GeneralReview
        from structured_service import StructuredReviewService
    else:
        from .structured_models import ComprehensiveContractReview, ContractSubjectReview, PaymentClauseReview, BreachClauseReview, GeneralReview
        from .structured_service import StructuredReviewService
    # 创建结构化审查服务实例
    structured_review_service = StructuredReviewService()
    print("✅ 结构化审查服务加载成功")
except ImportError as e:
    print(f"⚠️  结构化审查服务导入失败: {e}")
    structured_review_service = None

# 使用新的 lifespan 事件处理器替代已弃用的 on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动事件
    print("ContractAudit Chat System starting up...")
    print(f"Active sessions: {len(chat_manager.sessions)}")
    
    yield
    
    # 关闭事件
    print("ContractAudit Chat System shutting down...")
    print(f"Cleaning up {len(chat_manager.sessions)} sessions")

# 创建FastAPI应用
app = FastAPI(
    title="ContractAudit Chat System",
    description="基于LangChain的合同审计对话系统",
    version="1.0.0",
    lifespan=lifespan  # 使用新的 lifespan 事件处理器
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含外部路由
app.include_router(external_router, prefix="/api", tags=["external"])
print("✅ 已包含外部路由 (external_routes)")

# Pydantic模型
class CreateSessionRequest(BaseModel):
    user_id: str
    contract_file: Optional[str] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str

class LoadContractRequest(BaseModel):
    session_id: str
    contract_file: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    context_used: Optional[str] = None
    timestamp: str
    error: Optional[bool] = False

class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    contract_file: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int

# 流式输出事件模型
class StreamEventData(BaseModel):
    """流式输出事件数据模型"""
    content: Optional[str] = None
    token_index: Optional[int] = None
    is_final: Optional[bool] = None
    role: Optional[str] = None
    session_id: Optional[str] = None
    question: Optional[str] = None
    status: Optional[str] = None
    context_length: Optional[int] = None
    prompt_length: Optional[int] = None
    total_tokens: Optional[int] = None
    error: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None

class StreamEvent(BaseModel):
    """流式输出事件模型"""
    event: str  # start, context_ready, token, complete, error
    timestamp: float
    data: StreamEventData

# 保存审查结果的模型
class SaveReviewRequest(BaseModel):
    """保存审查结果请求模型"""
    session_id: str = Field(..., description="会话ID")
    structured_result: Dict[str, Any] = Field(..., description="结构化审查结果")
    user_id: Optional[str] = Field(None, description="用户ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    reviewer: Optional[str] = Field("AI助手", description="审查人")

class SaveReviewResponse(BaseModel):
    """保存审查结果响应模型"""
    message: str = Field(..., description="响应消息")
    review_id: int = Field(..., description="保存的审查记录ID")
    session_id: str = Field(..., description="会话ID")
    saved_at: str = Field(..., description="保存时间")

class MultipleSaveReviewRequest(BaseModel):
    """批量保存审查结果请求模型"""
    reviews: List[Dict[str, Any]] = Field(..., description="审查结果列表")
    user_id: Optional[str] = Field(None, description="用户ID")

class MultipleSaveReviewResponse(BaseModel):
    """批量保存审查结果响应模型"""
    message: str = Field(..., description="响应消息")
    saved_count: int = Field(..., description="成功保存的数量")
    review_ids: List[int] = Field(..., description="保存的审查记录ID列表")

# 路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ContractAudit Chat System",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/sessions", response_model=Dict[str, str])
async def create_session(request: CreateSessionRequest):
    """创建新的聊天会话"""
    try:
        session_id = chat_manager.create_session(
            user_id=request.user_id,
            contract_file=request.contract_file
        )
        return {
            "session_id": session_id,
            "message": "Session created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送聊天消息"""
    try:
        result = chat_manager.chat(request.session_id, request.message)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream", response_model=StreamEvent)
async def chat_stream(request: ChatRequest):
    """
    SSE流式聊天接口，真实 Ark LLM 流式输出。
    
    返回结构化事件流，包含以下事件类型：
    - start: 开始处理请求
    - context_ready: 上下文检索完成
    - token: 每个token的输出
    - complete: 输出完成
    - error: 错误事件
    
    每个事件包含 event、timestamp、data 字段。
    """
    import json
    import sys
    
    def event_stream():
        print(f"[DEBUG] /chat/stream called with session_id={request.session_id}, message={request.message}", file=sys.stderr)
        yielded = False
        for event_data in chat_manager.chat_stream(request.message, request.session_id):
            print(f"[DEBUG] Yielding event: {event_data}", file=sys.stderr)
            yielded = True
            if isinstance(event_data, dict):
                if 'data' in event_data and isinstance(event_data['data'], dict):
                    event_data['data']['session_id'] = request.session_id
                    event_data['data']['role'] = 'assistant'
                json_data = json.dumps(event_data, ensure_ascii=False)
                yield f"data: {json_data}\n\n"
        if not yielded:
            print("[ERROR] No events yielded by chat_manager.chat_stream!", file=sys.stderr)
    
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/sessions/{session_id}/load-contract")
async def load_contract(session_id: str, request: LoadContractRequest):
    """为会话加载合同文档"""
    try:
        # 验证会话存在
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 验证文件存在
        if not os.path.exists(request.contract_file):
            raise HTTPException(status_code=404, detail="Contract file not found")
        
        # 加载合同到向量存储
        success = chat_manager.load_contract_to_vectorstore(request.contract_file)
        
        if success:
            # 更新会话信息
            session.contract_file = request.contract_file
            return {
                "message": "Contract loaded successfully",
                "contract_file": request.contract_file
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load contract")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str):
    """获取会话详情和历史"""
    try:
        session_data = chat_manager.get_session_history(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(user_id: Optional[str] = None):
    """列出所有会话"""
    try:
        sessions = chat_manager.list_sessions(user_id)
        session_infos = []
        
        for session_data in sessions:
            session_info = SessionInfo(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                contract_file=session_data["contract_file"],
                created_at=session_data["created_at"],
                updated_at=session_data["updated_at"],
                message_count=len(session_data["messages"])
            )
            session_infos.append(session_info)
        
        return session_infos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        success = chat_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        stats = chat_manager.get_system_stats()
        return {
            "status": "healthy",
            "sessions_count": stats.get("total_sessions", 0),
            "vector_store_available": stats.get("vector_store_available", False),
            "llm_client_available": stats.get("llm_client_available", False),
            "embeddings_available": stats.get("embeddings_available", False),
            "ark_available": stats.get("ark_available", False)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "sessions_count": 0,
            "vector_store_available": False,
            "llm_client_available": False,
            "embeddings_available": False,
            "ark_available": False
        }

@app.get("/test/stream")
async def stream_test_page():
    """流式输出测试页面"""
    # 获取当前文件所在目录的上级目录（rag642目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    test_file_path = os.path.join(parent_dir, "stream_test.html")
    
    if os.path.exists(test_file_path):
        return FileResponse(test_file_path, media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="Test page not found")

@app.get("/test/stream-simple")
async def stream_test_simple():
    """简单的流式输出测试页面（内嵌HTML）"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>简单流式测试</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .output { border: 1px solid #ccc; padding: 10px; height: 300px; overflow-y: auto; background: #f9f9f9; }
        .event { margin: 5px 0; padding: 5px; border-left: 3px solid #007bff; }
        .token { border-left-color: #28a745; }
        .complete { border-left-color: #ffc107; }
        .error { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <h2>🚀 流式输出测试</h2>
    <div>
        <input type="text" id="message" value="请分析这个合同的风险点" style="width: 300px; padding: 5px;">
        <button onclick="startStream()">开始测试</button>
        <button onclick="clearOutput()">清空</button>
    </div>
    <div class="output" id="output"></div>
    
    <script>
        function startStream() {
            const message = document.getElementById('message').value;
            const output = document.getElementById('output');
            output.innerHTML = '<p>开始流式输出...</p>';
            
            fetch('/chat/stream', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: 'test', message: message})
            })
            .then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                function readStream() {
                    return reader.read().then(({done, value}) => {
                        if (done) return;
                        
                        buffer += decoder.decode(value, {stream: true});
                        const lines = buffer.split('\\n');
                        buffer = lines.pop();
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const eventData = JSON.parse(line.substring(6));
                                    addEvent(eventData);
                                } catch (e) {
                                    console.error('JSON解析错误:', e);
                                }
                            }
                        }
                        
                        return readStream();
                    });
                }
                
                return readStream();
            })
            .catch(error => {
                output.innerHTML += '<p style="color: red;">错误: ' + error.message + '</p>';
            });
        }
        
        function addEvent(eventData) {
            const output = document.getElementById('output');
            const div = document.createElement('div');
            div.className = 'event ' + eventData.event;
            div.innerHTML = '<strong>' + eventData.event + '</strong>: ' + JSON.stringify(eventData.data);
            output.appendChild(div);
            output.scrollTop = output.scrollHeight;
        }
        
        function clearOutput() {
            document.getElementById('output').innerHTML = '';
        }
    </script>
</body>
</html>
    """
    return FileResponse(
        path=None,
        content=html_content.encode('utf-8'),
        media_type="text/html"
    )

@app.post("/chat/confirm")
async def chat_confirm(request: Request):
    log_debug("收到confirm请求")
    print("收到confirm请求")
    """
    前端确认后，才进行真实大模型调用并流式输出结构化审查结果。
    支持审查规则解析和四种审查类型：合同主体审查、付款条款审查、违约条款审查、通用审查
    请求体需包含 session_id 和 message。
    """
    import json
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message")
    auto_save = data.get("auto_save", False)  # 新增自动保存选项
    user_id = data.get("user_id")  # 新增用户ID
    project_name = data.get("project_name")  # 新增项目名称
    
    if not session_id or not message:
        raise HTTPException(status_code=400, detail="session_id 和 message 必填")
    
    # 解析 message 中的审查规则信息
    review_rules = None
    review_stage = None
    review_list_count = 0
    
    try:
        # 尝试解析 message 为 JSON
        message_data = json.loads(message)
        review_stage = message_data.get("reviewStage")
        review_list_count = message_data.get("reviewList", 0)
        review_rules = message_data.get("reviewRules", [])
        contract_id = message_data.get("contract_id")  # 从message中提取合同ID
        print(f"[DEBUG] 解析到审查规则: {len(review_rules)} 条规则", file=sys.stderr)
    except (json.JSONDecodeError, TypeError):
        # 如果不是 JSON 格式，当作普通消息处理
        contract_id = None
        print(f"[DEBUG] message 不是 JSON 格式，作为普通消息处理: {message}", file=sys.stderr)
        pass
    
    # 确保contract_id和contract_name有值，即使前端没有传递
    if not contract_id:
        # 尝试从session_id生成contract_id
        contract_id = f"contract_{session_id}" if session_id else None
        print(f"[DEBUG] 使用session_id生成contract_id: {contract_id}", file=sys.stderr)
    
    if not project_name:
        # 尝试从session_id生成project_name
        project_name = f"项目_{session_id}" if session_id else "默认项目"
        print(f"[DEBUG] 使用session_id生成project_name: {project_name}", file=sys.stderr)

    async def event_stream():
        import json
        import time
        import sys
        import asyncio
        
        start_time = time.time()
        
        try:
            # 规则id到原始rule的映射，便于查找分组信息
            rule_id_to_rule = {rule.get('id', 0): rule for rule in review_rules} if review_rules else {}
            
            # 检查结构化审查服务是否可用
            if structured_review_service is None:
                raise Exception("结构化审查服务未加载，请检查相关模块")
            
            # 获取合同内容
            contract_content = getattr(chat_manager, 'contract_content', 'No contract content available')
            if hasattr(chat_manager, '_simple_text_store') and chat_manager._simple_text_store:
                contract_content = "\n\n".join([doc.page_content for doc in chat_manager._simple_text_store[:3]])
            
            print(f"[DEBUG] contract_content length: {len(contract_content)}", file=sys.stderr)
            print(f"[DEBUG] contract_content preview: {contract_content[:200]}...", file=sys.stderr)
            
            # 发送开始事件
            event_data = {
                "event": "start",
                "timestamp": time.time(),
                "data": {
                    "message": message,
                    "session_id": session_id,
                    "status": "processing",
                    "review_stage": review_stage,
                    "review_rules_count": len(review_rules) if review_rules else 0,
                    "review_types": [f"Rule {i+1}: {rule.get('ruleName', '未命名规则')}" for i, rule in enumerate(review_rules)] if review_rules else []
                }
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 如果有审查规则，处理审查规则
            if review_rules and len(review_rules) > 0:
                print(f"[DEBUG] 开始处理 {len(review_rules)} 条审查规则", file=sys.stderr)
                
                # 发送规则处理开始事件
                event_data = {
                    "event": "rules_processing_started",
                    "timestamp": time.time(),
                    "data": {
                        "session_id": session_id,
                        "status": "rules_processing",
                        "total_rules": len(review_rules),
                        "processed_rules": 0,
                        "message": f"开始处理 {len(review_rules)} 条审查规则"
                    }
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                
                # 异步处理每个审查规则
                rule_results = []
                processed_count = 0
                
                async def process_single_rule(rule, rule_index):
                    """处理单个审查规则"""
                    try:
                        from volcenginesdkarkruntime import AsyncArk
                        
                        # 创建异步Ark客户端
                        async_ark_client = AsyncArk(
                            api_key=chat_manager.ark_api_key,
                        )
                        
                        # 构建规则审查提示词
                        rule_prompt = f"""
你是一个专业的合同审查助手。请根据以下审查规则对合同内容进行分析。

审查规则信息：
- 规则名称：{rule.get('ruleName', '未命名规则')}
- 规则类型：{rule.get('type', '未知类型')}
- 风险等级：{rule.get('riskLevel', '未知等级')}
- 风险归属：{rule.get('riskAttributionName', '未知归属')}
- 规则分组：{rule.get('ruleGroupName', '未分组')}
- 修改意见：{rule.get('reviseOpinion', '无')}

条件信息：
{rule.get('conditionList', [])}

合同内容：
{contract_content}

请输出以下格式的JSON（必须使用中文）：
{{
    "rule_id": {rule.get('id', 0)},
    "rule_name": "{rule.get('ruleName', '未命名规则')}",
    "review_result": "通过|不通过",
    "risk_level": "high|medium|low|none",
    "matched_content": "匹配到的合同内容片段",
    "analysis": "详细的分析说明",
    "issues": [
        "具体问题1的详细描述",
        "具体问题2的详细描述"
    ],
    "suggestions": [
        "具体建议1，包含可执行的步骤",
        "具体建议2，包含可执行的步骤"
    ],
    "confidence_score": 0.85
}}

重要要求：
1. 必须输出有效的JSON格式
2. 必须使用中文输出所有内容
3. 根据规则条件对合同内容进行匹配分析
4. 提供详细的分析说明和具体建议
5. 如果合同内容不匹配规则条件，也要给出合理的分析结果
"""
                        
                        # 调用模型进行规则审查
                        response = await async_ark_client.chat.completions.create(
                            model=chat_manager.ark_model,
                            messages=[
                                {"role": "system", "content": "你是一个专业的合同审查助手，必须输出有效的JSON格式，所有内容必须使用中文。"},
                                {"role": "user", "content": rule_prompt},
                            ],
                        )
                        
                        response_text = response.choices[0].message.content
                        
                        # 解析响应
                        try:
                            rule_result = json.loads(response_text)
                            rule_result['rule_index'] = rule_index
                            rule_result['rule_id'] = rule.get('id', 0)
                            rule_result['rule_name'] = rule.get('ruleName', '未命名规则')
                            return rule_result
                        except json.JSONDecodeError:
                            print(f"[WARN] 规则 {rule.get('ruleName')} JSON解析失败，使用默认结果", file=sys.stderr)
                            return {
                                "rule_id": rule.get('id', 0),
                                "rule_name": rule.get('ruleName', '未命名规则'),
                                "review_result": "不通过",
                                "risk_level": "medium",
                                "matched_content": "无法解析响应",
                                "analysis": "模型响应解析失败",
                                "issues": ["响应格式错误"],
                                "suggestions": ["重新审查规则"],
                                "confidence_score": 0.5,
                                "rule_index": rule_index
                            }
                            
                    except Exception as e:
                        print(f"[ERROR] 处理规则 {rule.get('ruleName')} 失败: {e}", file=sys.stderr)
                        return {
                            "rule_id": rule.get('id', 0),
                            "rule_name": rule.get('ruleName', '未命名规则'),
                            "review_result": "不通过",
                            "risk_level": "high",
                            "matched_content": "处理失败",
                            "analysis": f"规则处理异常: {str(e)}",
                            "issues": ["规则处理失败"],
                            "suggestions": ["检查规则配置"],
                            "confidence_score": 0.3,
                            "rule_index": rule_index
                        }
                
                # 创建规则处理任务
                rule_tasks = [process_single_rule(rule, i) for i, rule in enumerate(review_rules)]
                
                # 实时处理完成的规则
                for completed_rule_task in asyncio.as_completed(rule_tasks):
                    try:
                        rule_result = await completed_rule_task
                        processed_count += 1
                        
                        print(f"[DEBUG] 规则 {rule_result['rule_name']} 处理完成 ({processed_count}/{len(review_rules)})", file=sys.stderr)
                        
                        rule_results.append(rule_result)
                        
                        # 在 rule_completed 事件前，补充分组和枚举
                        rule_group_id = rule_id_to_rule.get(rule_result.get("rule_id", 0), {}).get("ruleGroupId")
                        rule_group_name = rule_id_to_rule.get(rule_result.get("rule_id", 0), {}).get("ruleGroupName")
                        review_result_enum = "FAIL" if rule_result.get("review_result") in ["不通过", "FAIL"] else "PASS"
                        completed_rule = dict(rule_result)
                        completed_rule["ruleGroupId"] = rule_group_id
                        completed_rule["ruleGroupName"] = rule_group_name
                        completed_rule["review_result"] = review_result_enum
                        # 发送单个规则完成事件
                        event_data = {
                            "event": "rule_completed",
                            "timestamp": time.time(),
                            "data": {
                                "session_id": session_id,
                                "status": "rule_completed",
                                "completed_rule": completed_rule,
                                "processed_count": processed_count,
                                "total_rules": len(review_rules),
                                "message": f"规则 {rule_result['rule_name']} 审查完成"
                            }
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                        
                    except Exception as e:
                        processed_count += 1
                        print(f"[ERROR] 规则处理异常: {e}", file=sys.stderr)
                        
                        # 发送规则失败事件
                        event_data = {
                            "event": "rule_failed",
                            "timestamp": time.time(),
                            "data": {
                                "session_id": session_id,
                                "status": "rule_failed",
                                "failed_rule_index": processed_count - 1,
                                "processed_count": processed_count,
                                "total_rules": len(review_rules),
                                "error": str(e),
                                "message": f"规则 {processed_count} 处理失败"
                            }
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                
                # 发送规则处理完成事件
                event_data = {
                    "event": "rules_processing_completed",
                    "timestamp": time.time(),
                    "data": {
                        "session_id": session_id,
                        "status": "rules_completed",
                        "total_rules": len(review_rules),
                        "processed_rules": len(rule_results),
                        "rule_results": rule_results,
                        "message": f"所有 {len(review_rules)} 条审查规则处理完成"
                    }
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 如果没有审查规则，返回错误
            if not review_rules or len(review_rules) == 0:
                event_data = {
                    "event": "error",
                    "timestamp": time.time(),
                    "data": {
                        "session_id": session_id,
                        "error": "未提供审查规则",
                        "status": "failed",
                        "message": "请在前端message中提供审查规则"
                    }
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                return
            
            # 构建基于规则的综合结果
            try:
                # 计算统计信息
                total_issues = 0
                high_risk_items = 0
                medium_risk_items = 0
                low_risk_items = 0
                critical_recommendations = []
                action_items = []
                
                for rule_result in rule_results:
                    if isinstance(rule_result, dict):
                        # 统计问题数量
                        total_issues += len(rule_result.get("issues", []))
                        
                        # 统计风险等级
                        risk_level = rule_result.get("risk_level", "medium")
                        if risk_level == "high":
                            high_risk_items += 1
                        elif risk_level == "medium":
                            medium_risk_items += 1
                        elif risk_level == "low":
                            low_risk_items += 1
                        
                        # 收集建议
                        suggestions = rule_result.get("suggestions", [])
                        action_items.extend(suggestions)
                        
                        # 收集关键建议
                        if risk_level in ["high", "medium"]:
                            critical_recommendations.extend(suggestions[:2])  # 只取前2个建议
                
                # 构建综合结果
                combined_result = {
                    "contract_name": "Contract Review",
                    "overall_risk_level": "high" if high_risk_items > 0 else "medium" if medium_risk_items > 0 else "low",
                    "total_issues": total_issues,
                    "high_risk_items": high_risk_items,
                    "medium_risk_items": medium_risk_items,
                    "low_risk_items": low_risk_items,
                    "overall_summary": f"基于 {len(review_rules)} 条规则的合同审查完成，发现 {total_issues} 个问题",
                    "critical_recommendations": critical_recommendations[:5],  # 最多5个关键建议
                    "action_items": action_items[:10],  # 最多10个行动项
                    "confidence_score": 0.8,
                    "rule_results": rule_results
                }
                
                response_text = json.dumps(combined_result, ensure_ascii=False)
                print(f"[DEBUG] 规则审查结果完成，总长度: {len(response_text)}", file=sys.stderr)
                
            except Exception as e:
                print(f"[ERROR] 构建规则审查结果失败: {e}", file=sys.stderr)
                response_text = "{}"
            
            # 解析结构化响应
            try:
                # 直接解析合并后的JSON结果
                structured_dict = json.loads(response_text)
                
                # 创建简化的结构化结果对象
                structured_result = type('StructuredResult', (), {
                    'contract_name': structured_dict.get("contract_name", "Contract Review"),
                    'overall_risk_level': structured_dict.get("overall_risk_level", "medium"),
                    'total_issues': structured_dict.get("total_issues", 0),
                    'high_risk_items': structured_dict.get("high_risk_items", 0),
                    'medium_risk_items': structured_dict.get("medium_risk_items", 0),
                    'low_risk_items': structured_dict.get("low_risk_items", 0),
                    'overall_summary': structured_dict.get("overall_summary", ""),
                    'critical_recommendations': structured_dict.get("critical_recommendations", []),
                    'action_items': structured_dict.get("action_items", []),
                    'confidence_score': structured_dict.get("confidence_score", 0.8),
                    'review_duration': 0.0,
                    'model_used': 'rule_based_review',
                    'dict': lambda self: structured_dict
                })()
                
            except Exception as e:
                print(f"[ERROR] Failed to parse structured response: {e}", file=sys.stderr)
                # 创建默认的结构化结果
                structured_result = type('StructuredResult', (), {
                    'contract_name': "Contract Review",
                    'overall_risk_level': "medium",
                    'total_issues': 0,
                    'high_risk_items': 0,
                    'medium_risk_items': 0,
                    'low_risk_items': 0,
                    'overall_summary': "规则审查解析失败",
                    'critical_recommendations': ["请检查规则配置"],
                    'action_items': ["重新提交审查请求"],
                    'confidence_score': 0.5,
                    'review_duration': 0.0,
                    'model_used': 'rule_based_review',
                    'dict': lambda self: {
                        "contract_name": "Contract Review",
                        "overall_risk_level": "medium",
                        "total_issues": 0,
                        "high_risk_items": 0,
                        "medium_risk_items": 0,
                        "low_risk_items": 0,
                        "overall_summary": "规则审查解析失败",
                        "critical_recommendations": ["请检查规则配置"],
                        "action_items": ["重新提交审查请求"],
                        "confidence_score": 0.5
                    }
                })()
            
            # 计算处理时间
            processing_time = time.time() - start_time
            structured_result.review_duration = processing_time
            
            # 安全序列化结构化结果
            try:
                structured_dict = structured_result.dict()
                # 确保所有值都是可序列化的
                def clean_dict(obj):
                    if isinstance(obj, dict):
                        return {k: clean_dict(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_dict(item) for item in obj]
                    elif hasattr(obj, 'isoformat'):  # datetime对象
                        return obj.isoformat()
                    else:
                        return str(obj) if obj is not None else None
                
                structured_dict = clean_dict(structured_dict)
                print(f"[DEBUG] structured_dict keys: {list(structured_dict.keys())}", file=sys.stderr)
                print(f"[DEBUG] structured_dict has subject_review: {'subject_review' in structured_dict}", file=sys.stderr)
                
            except Exception as e:
                print(f"[ERROR] 序列化结构化结果失败: {e}", file=sys.stderr)
                # 创建简化的结构化数据
                structured_dict = {
                    "contract_name": "Contract Review",
                    "overall_risk_level": "medium",
                    "total_issues": 1,
                    "high_risk_items": 0,
                    "medium_risk_items": 1,
                    "low_risk_items": 0,
                    "confidence_score": 0.5,
                    "overall_summary": "Serialization error occurred during review",
                    "critical_recommendations": ["Please check contract content"],
                    "action_items": ["Resubmit contract content"]
                }
            
            # 发送结构化结果事件
            event_data = {
                "event": "structured_result",
                "timestamp": time.time(),
                "data": {
                    "session_id": session_id,
                    "status": "success",
                    "total": structured_dict.get("total_issues", 0) or 0,
                    "failed_count": (structured_dict.get("high_risk_items", 0) or 0) + (structured_dict.get("medium_risk_items", 0) or 0),
                    "passed_count": structured_dict.get("low_risk_items", 0) or 0,
                    "completed_tasks": len(rule_results),
                    "total_tasks": len(review_rules),
                    "review_stage": review_stage,
                    "review_rules_count": len(review_rules) if review_rules else 0,
                    # 包含规则审查结果
                    "rule_results": rule_results if 'rule_results' in locals() else [],
                    "list": [
                        {
                            "result": 1 if rule_result.get("review_result") in ["不通过", "FAIL"] else 0,  # 0=pass, 1=fail
                            "riskLevel": 2 if rule_result.get("risk_level") == "high" else 1 if rule_result.get("risk_level") == "medium" else 0,  # 0=low risk, 1=medium risk, 2=high risk
                            "atrributable": 1,  # whether attributable
                            "ruleName": rule_result.get("rule_name", "未命名规则"),
                            "ruleId": rule_result.get("rule_id", 0),
                            "ruleIndex": rule_result.get("rule_index", 0),
                            "original_content": rule_result.get("matched_content", contract_content[:200] + "..." if len(contract_content) > 200 else contract_content),
                            "modification_suggestion": rule_result.get("suggestions", [""])[0] if rule_result.get("suggestions") else "",
                            "risk_description": rule_result.get("analysis", "无风险描述"),
                            "confidence_score": rule_result.get("confidence_score", 0.5),
                            # 新增分组信息
                            "ruleGroupId": rule_id_to_rule.get(rule_result.get("rule_id", 0), {}).get("ruleGroupId"),
                            "ruleGroupName": rule_id_to_rule.get(rule_result.get("rule_id", 0), {}).get("ruleGroupName"),
                            # review_result 用枚举
                            "review_result": "FAIL" if rule_result.get("review_result") in ["不通过", "FAIL"] else "PASS"
                        }
                        for rule_result in (rule_results if 'rule_results' in locals() else [])
                    ]
                }
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 发送完成事件
            event_data = {
                "event": "complete",
                "timestamp": time.time(),
                "data": {
                    "session_id": session_id,
                    "status": "success",
                    "final_message": "Structured review completed"
                }
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
            # 自动保存逻辑 - 只要有规则结果就自动保存
            if rule_results:
                log_debug(f"[DEBUG] 进入自动保存逻辑，rule_results长度={len(rule_results)}")
                print(f"[DEBUG] 进入自动保存逻辑，rule_results长度={len(rule_results)}")
                try:
                    from ContractAudit.models import (
                        create_confirm_review_session,
                        bulk_create_confirm_review_rule_results
                    )
                    from ContractAudit.config import get_session
                    
                    # 获取数据库会话
                    db = next(get_session())
                    
                    # 准备会话数据
                    session_data = {
                        'session_id': session_id,
                        'user_id': user_id,
                        'project_name': project_name,
                        'review_stage': review_stage,
                        'review_rules_count': len(review_rules) if review_rules else 0,
                        'total_issues': structured_dict.get("total_issues", 0),
                        'high_risk_items': structured_dict.get("high_risk_items", 0),
                        'medium_risk_items': structured_dict.get("medium_risk_items", 0),
                        'low_risk_items': structured_dict.get("low_risk_items", 0),
                        'overall_risk_level': structured_dict.get("overall_risk_level", "medium"),
                        'overall_summary': structured_dict.get("overall_summary", ""),
                        'confidence_score': int(float(structured_dict.get("confidence_score", 0.8)) * 100),
                        'critical_recommendations': structured_dict.get("critical_recommendations", []),
                        'action_items': structured_dict.get("action_items", []),
                        'processing_time': int(processing_time),
                        'model_used': 'rule_based_review',
                        'status': 'completed'
                    }
                    
                    # 创建会话记录
                    confirm_session = create_confirm_review_session(db, session_data)
                    
                    # 准备规则结果数据
                    log_debug(f"[DEBUG] 开始准备规则结果数据，原始 rule_results 数量: {len(rule_results)}")
                    rule_results_data = []
                    for i, rule_result in enumerate(rule_results):
                        log_debug(f"[DEBUG] 处理第 {i+1} 个规则结果: {rule_result}")
                        try:
                            confidence_score = float(rule_result.get('confidence_score', 0.5))
                        except (ValueError, TypeError):
                            confidence_score = 0.5
                        result_data = {
                            'session_id': session_id,
                            'rule_id': rule_result.get('rule_id', 0),
                            'rule_name': rule_result.get('rule_name', '未命名规则'),
                            'rule_index': rule_result.get('rule_index', 0),
                            'review_result': rule_result.get('review_result', '不通过'),
                            'risk_level': rule_result.get('risk_level', 'medium'),
                            'matched_content': rule_result.get('matched_content', ''),
                            'analysis': rule_result.get('analysis', ''),
                            'issues': rule_result.get('issues', []),
                            'suggestions': rule_result.get('suggestions', []),
                            'confidence_score': int(confidence_score * 100),
                            'user_feedback': rule_result.get('user_feedback', None),
                            'contract_id': contract_id,  # 新增：存合同ID
                            'contract_name': project_name,  # 新增：存合同名称
                            # 新增：存 risk_attribution_id，优先取 rule_result，再取 rule_id_to_rule
                            'risk_attribution_id': (
                                rule_result.get('riskAttributionId')
                                if rule_result.get('riskAttributionId') is not None else
                                rule_result.get('risk_attribution_id')
                                if rule_result.get('risk_attribution_id') is not None else
                                rule_id_to_rule.get(rule_result.get('rule_id', 0), {}).get('riskAttributionId')
                            ),
                        }
                        log_debug(f"[DEBUG] 构建的 result_data: {result_data}")
                        rule_results_data.append(result_data)
                    log_debug(f"[DEBUG] 准备调用 bulk_create_confirm_review_rule_results，数据条数: {len(rule_results_data)}")
                    # 批量创建规则结果记录
                    if rule_results_data:
                        try:
                            created_results = bulk_create_confirm_review_rule_results(db, rule_results_data)
                            log_debug(f"[DEBUG] bulk_create_confirm_review_rule_results 返回结果: {created_results}")
                        except Exception as e:
                            log_debug(f"[ERROR] bulk_create_confirm_review_rule_results 异常: {e}")
                    else:
                        log_debug(f"[DEBUG] rule_results_data 为空，跳过数据库写入")
                    
                    # 发送自动保存成功事件
                    event_data = {
                        "event": "auto_save_success",
                        "timestamp": time.time(),
                        "data": {
                            "session_id": session_id,
                            "message": "审查结果已自动保存到数据库",
                            "saved_session_id": confirm_session.id,
                            "saved_rule_results_count": len(rule_results_data),
                            "user_id": user_id,
                            "project_name": project_name
                        }
                    }
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                    
                except Exception as e:
                    print(f"[ERROR] 自动保存失败: {e}", file=sys.stderr)
                    # 发送自动保存失败事件
                    event_data = {
                        "event": "auto_save_failed",
                        "timestamp": time.time(),
                        "data": {
                            "session_id": session_id,
                            "error": str(e),
                            "message": "自动保存失败，请手动保存"
                        }
                    }
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            else:
                # 发送保存提示事件
                event_data = {
                    "event": "save_available",
                    "timestamp": time.time(),
                    "data": {
                        "session_id": session_id,
                        "message": "审查完成，可以保存结果到数据库",
                        "save_endpoint": "/chat/save-review",
                        "auto_save": auto_save,
                        "user_id": user_id,
                        "project_name": project_name,
                        "structured_result": structured_dict
                    }
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error_time = time.time()
            print(f"[ERROR] 流式处理异常: {e}", file=sys.stderr)
            import traceback
            print(f"[ERROR] 异常详情: {traceback.format_exc()}", file=sys.stderr)
            
            event_data = {
                "event": "error",
                "timestamp": error_time,
                "data": {
                    "session_id": session_id,
                    "error": str(e),
                    "status": "failed",
                    "processing_time": error_time - start_time,
                    "error_type": type(e).__name__
                }
            }
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
    
    from starlette.responses import StreamingResponse
    import asyncio
    
    # 将异步生成器转换为同步生成器
    def sync_event_stream():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = event_stream()
            while True:
                try:
                    yield loop.run_until_complete(async_gen.__anext__())
                except StopAsyncIteration:
                    break
        finally:
            loop.close()
    
    return StreamingResponse(
        sync_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# 新增：单独的结构化审查接口
@app.post("/chat/structured-review")
async def structured_review(request: ChatRequest):
    """
    直接返回结构化审查结果（非流式）
    """
    try:
        # 获取合同内容
        contract_content = getattr(chat_manager, 'contract_content', 'No contract content available')
        if hasattr(chat_manager, '_simple_text_store') and chat_manager._simple_text_store:
            contract_content = "\n\n".join([doc.page_content for doc in chat_manager._simple_text_store[:3]])
        
        # 创建结构化审查提示词
        structured_prompt = structured_review_service.create_comprehensive_prompt(contract_content)
        
        # 使用异步方式调用大模型
        from volcenginesdkarkruntime import AsyncArk
        
        # 创建异步Ark客户端
        async_ark_client = AsyncArk(
            api_key=chat_manager.ark_api_key,
        )
        
        # 异步调用大模型
        response = await async_ark_client.chat.completions.create(
            model=chat_manager.ark_model,
            messages=[
                {"role": "system", "content": "You are a professional contract review assistant. Please strictly follow the required JSON format to output four types of review results."},
                {"role": "user", "content": structured_prompt},
            ],
        )
        
        response_text = response.choices[0].message.content
        
        # 解析结构化响应
        structured_result = structured_review_service.parse_comprehensive_response(response_text)
        
        # 如果解析失败，使用备用响应
        if not structured_result:
            structured_result = structured_review_service.create_fallback_response(contract_content)
        
        return {
            "session_id": request.session_id,
            "status": "success",
            "structured_data": structured_result.dict(),
            "raw_response": response_text,
            "review_types": ["Contract Subject Review", "Payment Terms Review", "Breach Terms Review", "General Review"]
        }
        
    except Exception as e:
        return {
            "session_id": request.session_id,
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

# 调试接口 - 测试 JSON body 解析
@app.post("/debug/save-review")
async def debug_save_review(request: Request):
    """调试接口：直接打印收到的 JSON body"""
    try:
        data = await request.json()
        print(f"[DEBUG] 收到的原始数据: {data}")
        return {
            "message": "调试成功",
            "received_data": data,
            "data_type": str(type(data))
        }
    except Exception as e:
        print(f"[DEBUG] 解析 JSON 失败: {e}")
        return {
            "message": "解析失败",
            "error": str(e)
        }

# 保存审查结果接口
@app.post("/chat/save-review", response_model=SaveReviewResponse)
async def save_review_result(request: Request, db: Session = Depends(get_session)):
    """
    保存审查结果到数据库
    
    将结构化审查结果保存到 contract_audit_review 表中
    """
    try:
        from datetime import datetime
        
        # 手动解析 JSON 数据
        data = await request.json()
        print(f"[DEBUG] 收到的数据: {data}")
        
        # 验证必需字段
        session_id = data.get("session_id")
        structured_result = data.get("structured_result", {})
        user_id = data.get("user_id")
        project_name = data.get("project_name")
        reviewer = data.get("reviewer", "AI助手")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id 是必需的")
        if not structured_result:
            raise HTTPException(status_code=400, detail="structured_result 是必需的")
        
        # 从结构化结果中提取关键信息
        total_issues = structured_result.get("total_issues", 0)
        overall_risk_level = structured_result.get("overall_risk_level", "无")
        overall_summary = structured_result.get("overall_summary", "")
        
        # 确定审查状态
        review_status = "通过" if total_issues == 0 else "不通过"
        
        # 风险等级映射
        risk_level_map = {
            "high": "高",
            "medium": "中", 
            "low": "低",
            "none": "无"
        }
        risk_level = risk_level_map.get(overall_risk_level, "无")
        
        # 构建保存数据
        review_data = {
            "project_name": project_name or f"合同审查 - {session_id}",
            "risk_level": risk_level,
            "review_status": review_status,
            "reviewer": reviewer,
            "review_comment": overall_summary,
            "ext_json": {
                "structured_result": structured_result,
                "session_id": session_id,
                "user_id": user_id,
                "review_timestamp": datetime.now().isoformat(),
                "total_issues": total_issues,
                "high_risk_items": structured_result.get("high_risk_items", 0),
                "medium_risk_items": structured_result.get("medium_risk_items", 0),
                "low_risk_items": structured_result.get("low_risk_items", 0),
                "confidence_score": structured_result.get("confidence_score", 0.0)
            }
        }
        
        # 保存到数据库
        saved_review = create_contract_audit_review(db, review_data)
        
        return SaveReviewResponse(
            message="审查结果已成功保存",
            review_id=saved_review.id,
            session_id=session_id,
            saved_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存审查结果失败: {str(e)}")

@app.post("/chat/save-multiple-reviews", response_model=MultipleSaveReviewResponse)
async def save_multiple_reviews(request: MultipleSaveReviewRequest, db: Session = Depends(get_session)):
    """
    批量保存多个审查结果到数据库
    """
    try:
        from datetime import datetime
        
        saved_reviews = []
        
        for review_data in request.reviews:
            try:
                # 提取基本信息
                session_id = review_data.get("session_id")
                structured_result = review_data.get("structured_result", {})
                project_name = review_data.get("project_name", f"合同审查 - {session_id}")
                reviewer = review_data.get("reviewer", "AI助手")
                
                total_issues = structured_result.get("total_issues", 0)
                overall_risk_level = structured_result.get("overall_risk_level", "无")
                overall_summary = structured_result.get("overall_summary", "")
                
                # 确定审查状态和风险等级
                review_status = "通过" if total_issues == 0 else "不通过"
                risk_level_map = {
                    "high": "高", "medium": "中", "low": "低", "none": "无"
                }
                risk_level = risk_level_map.get(overall_risk_level, "无")
                
                # 构建保存数据
                db_review_data = {
                    "project_name": project_name,
                    "risk_level": risk_level,
                    "review_status": review_status,
                    "reviewer": reviewer,
                    "review_comment": overall_summary,
                    "ext_json": {
                        "structured_result": structured_result,
                        "session_id": session_id,
                        "user_id": request.user_id,
                        "review_timestamp": datetime.now().isoformat(),
                        "total_issues": total_issues,
                        "high_risk_items": structured_result.get("high_risk_items", 0),
                        "medium_risk_items": structured_result.get("medium_risk_items", 0),
                        "low_risk_items": structured_result.get("low_risk_items", 0),
                        "confidence_score": structured_result.get("confidence_score", 0.0)
                    }
                }
                
                # 保存到数据库
                saved_review = create_contract_audit_review(db, db_review_data)
                saved_reviews.append(saved_review)
                
            except Exception as e:
                print(f"[ERROR] 保存单个审查结果失败: {e}")
                continue
        
        return MultipleSaveReviewResponse(
            message=f"成功保存 {len(saved_reviews)} 个审查结果",
            saved_count=len(saved_reviews),
            review_ids=[r.id for r in saved_reviews]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量保存审查结果失败: {str(e)}")

@app.get("/chat/saved-reviews/{session_id}")
async def get_saved_reviews(session_id: str, db: Session = Depends(get_session)):
    """
    获取指定会话的已保存审查结果
    """
    try:
        from sqlalchemy import text
        
        # 查询包含指定session_id的审查记录
        reviews = db.query(ContractAuditReview).filter(
            ContractAuditReview.ext_json.contains({"session_id": session_id}),
            ContractAuditReview.is_deleted == False
        ).order_by(ContractAuditReview.created_at.desc()).all()
        
        # 格式化返回数据
        review_list = []
        for review in reviews:
            review_list.append({
                "id": review.id,
                "project_name": review.project_name,
                "risk_level": review.risk_level,
                "review_status": review.review_status,
                "reviewer": review.reviewer,
                "review_comment": review.review_comment,
                "created_at": review.created_at.isoformat(),
                "updated_at": review.updated_at.isoformat(),
                "ext_json": review.ext_json
            })
        
        return {
            "session_id": session_id,
            "total_count": len(review_list),
            "reviews": review_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取保存的审查结果失败: {str(e)}")

@app.delete("/chat/saved-reviews/{review_id}")
async def delete_saved_review(review_id: int, db: Session = Depends(get_session)):
    """
    删除指定的审查记录（软删除）
    """
    try:
        from ContractAudit.models import delete_contract_audit_review
        
        success = delete_contract_audit_review(db, review_id)
        
        if success:
            return {"message": "审查记录已删除", "review_id": review_id}
        else:
            raise HTTPException(status_code=404, detail="审查记录不存在")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除审查记录失败: {str(e)}")

# 启动事件
# @app.on_event("startup")
# async def startup_event():
#     """应用启动时的初始化"""
#     print("ContractAudit Chat System starting up...")
#     print(f"Active sessions: {len(chat_manager.sessions)}")

# 关闭事件
# @app.on_event("shutdown")
# async def shutdown_event():
#     """应用关闭时的清理"""
#     print("ContractAudit Chat System shutting down...")
#     print(f"Cleaning up {len(chat_manager.sessions)} sessions")

# 包含外部路由（如果可用）
if external_router is not None:
    app.include_router(external_router, prefix="/api")
    print("✅ 外部路由已加载，前缀: /api")
else:
    print("⚠️  外部路由未加载（直接运行模式或导入失败）")

# 最小化测试路由 - 绕过Pydantic模型解析
@app.post("/test/save-review")
async def test_save_review(request: Request, db: Session = Depends(get_session)):
    """
    最小化测试路由 - 手动解析JSON并直接写入数据库
    绕过Pydantic模型解析以避免参数冲突
    """
    try:
        import json
        from datetime import datetime
        
        # 手动解析JSON
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        print(f"[DEBUG] 接收到的原始数据: {data}")
        
        # 提取必要字段
        session_id = data.get("session_id")
        structured_result = data.get("structured_result", {})
        user_id = data.get("user_id", "test_user")
        project_name = data.get("project_name", f"测试审查 - {session_id}")
        reviewer = data.get("reviewer", "测试助手")
        
        if not session_id:
            return {"error": "缺少session_id字段"}
        
        # 计算基本信息
        total_issues = structured_result.get("total_issues", 0)
        overall_risk_level = structured_result.get("overall_risk_level", "无")
        overall_summary = structured_result.get("overall_summary", "测试审查摘要")
        
        # 确定审查状态和风险等级
        review_status = "通过" if total_issues == 0 else "不通过"
        risk_level_map = {
            "high": "高", "medium": "中", "low": "低", "none": "无"
        }
        risk_level = risk_level_map.get(overall_risk_level, "无")
        
        # 构建保存数据
        review_data = {
            "project_name": project_name,
            "risk_level": risk_level,
            "review_status": review_status,
            "reviewer": reviewer,
            "review_comment": overall_summary,
            "ext_json": {
                "structured_result": structured_result,
                "session_id": session_id,
                "user_id": user_id,
                "review_timestamp": datetime.now().isoformat(),
                "total_issues": total_issues,
                "high_risk_items": structured_result.get("high_risk_items", 0),
                "medium_risk_items": structured_result.get("medium_risk_items", 0),
                "low_risk_items": structured_result.get("low_risk_items", 0),
                "confidence_score": structured_result.get("confidence_score", 0.0)
            }
        }
        
        # 保存到数据库
        saved_review = create_contract_audit_review(db, review_data)
        
        return {
            "message": "测试路由：审查结果已成功保存",
            "review_id": saved_review.id,
            "session_id": session_id,
            "saved_at": datetime.now().isoformat(),
            "test_route": True
        }
        
    except json.JSONDecodeError as e:
        return {"error": f"JSON解析失败: {str(e)}"}
    except Exception as e:
        return {"error": f"保存失败: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    import signal
    import sys

    def handle_exit(sig, frame):
        print("\n[INFO] 收到退出信号，正在优雅关闭服务...")
        sys.exit(0)

    # 捕获 Ctrl+C (SIGINT) 和 kill (SIGTERM)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    print(f"启动服务器在 {host}:{port}")
    print("按 Ctrl+C 可优雅关闭服务")
    uvicorn.run(
        "ContractAudit.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="debug"
    )
