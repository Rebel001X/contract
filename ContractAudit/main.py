"""
ContractAudit模块主入口文件
简化的合同审计对话系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contextlib import asynccontextmanager
import os
LOG_PATH = os.path.join(os.path.dirname(__file__), 'confirm_debug.log')
def log_debug(msg):
    try:
        # 确保日志目录存在
        log_dir = os.path.dirname(LOG_PATH)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except (PermissionError, OSError, Exception) as e:
        # 如果无法写入日志文件，则只打印到控制台
        print(f"[LOG_DEBUG] {msg}")
        print(f"[LOG_DEBUG] 写入日志文件失败: {e}")

import re
import functools
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

# 统一的异常处理类
class ContractAuditException(Exception):
    """合同审计系统自定义异常基类"""
    def __init__(self, message: str, code: int = 500, error_type: str = "INTERNAL_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

class RuleConfirmException(ContractAuditException):
    """rule/confirm 接口异常"""
    def __init__(self, message: str, original_error: Optional[Exception] = None, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=500,
            error_type="RULE_CONFIRM_ERROR",
            details={
                "original_error": str(original_error) if original_error else None,
                "error_type": type(original_error).__name__ if original_error else None,
                **(details or {})
            }
        )

class ValidationException(ContractAuditException):
    """数据验证异常"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code=400,
            error_type="VALIDATION_ERROR",
            details={"field": field}
        )

class ExternalServiceException(ContractAuditException):
    """外部服务调用异常"""
    def __init__(self, service_name: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=f"{service_name} 服务调用失败: {message}",
            code=503,
            error_type="EXTERNAL_SERVICE_ERROR",
            details={
                "service_name": service_name,
                "original_error": str(original_error) if original_error else None,
                "error_type": type(original_error).__name__ if original_error else None
            }
        )

def standard_exception_handler(func):
    """标准异常处理装饰器"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ContractAuditException as e:
            # 处理自定义异常
            error_response = {
                "code": e.code,
                "message": e.message,
                "error_type": e.error_type,
                "details": e.details,
                "success": False
            }
            return JSONResponse(content=error_response, status_code=e.code)
        except Exception as e:
            # 处理其他未预期的异常
            error_response = {
                "code": 500,
                "message": f"系统内部错误: {str(e)}",
                "error_type": "INTERNAL_ERROR",
                "details": {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                "success": False
            }
            return JSONResponse(content=error_response, status_code=500)
    return wrapper

def create_error_response(code: int, message: str, error_type: str = "ERROR", details: Optional[Dict] = None) -> Dict[str, Any]:
    """创建标准错误响应格式"""
    return {
        "code": code,
        "message": message,
        "error_type": error_type,
        "details": details or {},
        "success": False
    }

import re

def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def dict_keys_to_snake(d):
    if isinstance(d, dict):
        return {camel_to_snake(k): dict_keys_to_snake(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [dict_keys_to_snake(i) for i in d]
    else:
        return d

def snake_to_camel(s):
    parts = s.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])

def dict_keys_to_camel(d):
    if isinstance(d, dict):
        return {snake_to_camel(k): dict_keys_to_camel(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [dict_keys_to_camel(i) for i in d]
    else:
        return d

if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "ContractAudit"


import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid
import json
import asyncio
import httpx

# 导入数据库相关模块
try:
    from ContractAudit.config import get_session
    from ContractAudit.models import ContractAuditReview, create_contract_audit_review
except ImportError:
    try:
        # 直接运行时使用绝对导入
        from config import get_session
        from models import ContractAuditReview, create_contract_audit_review
    except ImportError:
        # 创建备用数据库函数
        def get_session():
            """备用数据库会话获取函数"""
            class MockSession:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
                def add(self, obj):
                    pass
                def commit(self):
                    pass
                def close(self):
                    pass
            return MockSession()
        
        def create_contract_audit_review(session, **kwargs):
            """备用创建审查记录函数"""
            return {"id": 1, "status": "created"}
        
        class ContractAuditReview:
            """备用审查记录模型"""
            def __init__(self, **kwargs):
                self.id = kwargs.get('id', 1)
                self.session_id = kwargs.get('session_id', '')
                self.user_id = kwargs.get('user_id', '')
                self.structured_result = kwargs.get('structured_result', {})
        
        print("⚠️  使用备用数据库模块")

# 处理相对导入问题 - 支持直接运行和模块导入
# 添加项目根目录到Python路径


# 尝试导入外部路由
try:
    from ContractAudit.external_routes import router as external_router, ContractViewRequest
    print("成功导入external_routes（包内相对导入）")
except ImportError:
    try:
        from external_routes import router as external_router
        print("成功导入external_routes（绝对导入）")
    except ImportError:
        # 创建备用外部路由
        from fastapi import APIRouter
        external_router = APIRouter()
        
        @external_router.post("/external/rag-stream")
        async def external_rag_stream(request):
            return {"message": "备用外部路由"}
        
        print("⚠️  使用备用外部路由")

# 导入聊天管理器
try:
    # 尝试不同的导入方式
    try:
        from ContractAudit.chat import get_chat_manager, ChatSession
    except ImportError:
        from chat import get_chat_manager, ChatSession
    chat_manager = get_chat_manager()
    print("✅ 聊天管理器加载成功")
except ImportError as e:
    print(f"❌ 聊天管理器导入失败: {e}")
    # 创建一个简单的备用聊天管理器
    class SimpleChatManager:
        def __init__(self):
            self.sessions = {}
        
        def chat_stream(self, question: str, session_id: str = None):
            import time
            yield {
                "event": "start",
                "timestamp": time.time(),
                "data": {
                    "question": question,
                    "status": "processing",
                    "session_id": session_id,
                    "role": "assistant"
                }
            }
            
            response_text = "这是一个简化的回复。"
            for i, char in enumerate(response_text):
                time.sleep(0.05)
                yield {
                    "event": "token",
                    "timestamp": time.time(),
                    "data": {
                        "content": char,
                        "token_index": i + 1,
                        "is_final": False,
                        "session_id": session_id,
                        "role": "assistant"
                    }
                }
            
            yield {
                "event": "complete",
                "timestamp": time.time(),
                "data": {
                    "total_tokens": len(response_text),
                    "status": "success",
                    "session_id": session_id,
                    "role": "assistant",
                    "is_final": True
                }
            }
        
        def create_session(self, user_id: str, contract_file: Optional[str] = None) -> str:
            """创建会话"""
            import uuid
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "contract_file": contract_file,
                "created_at": time.time(),
                "updated_at": time.time(),
                "messages": []
            }
            return session_id
        
        def get_session(self, session_id: str):
            """获取会话"""
            return self.sessions.get(session_id)
        
        def get_session_history(self, session_id: str):
            """获取会话历史"""
            return self.sessions.get(session_id)
        
        def list_sessions(self, user_id: Optional[str] = None):
            """列出会话"""
            sessions = []
            for session in self.sessions.values():
                if user_id is None or session["user_id"] == user_id:
                    sessions.append(session)
            return sessions
        
        def load_contract_to_vectorstore(self, contract_file: str) -> bool:
            """加载合同到向量存储"""
            return True  # 简化实现
        
        def chat(self, question: str, session_id: str = None) -> str:
            """普通聊天"""
            return "这是一个简化的回复。"
        
        def delete_session(self, session_id: str) -> bool:
            """删除会话"""
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
        
        def cleanup_expired_sessions(self) -> int:
            """清理过期会话"""
            return 0  # 简化实现
    chat_manager = SimpleChatManager()
    print("⚠️  使用备用聊天管理器")

# 导入结构化审查相关模块
try:
    # 尝试不同的导入方式
    try:
        from structured_models import ComprehensiveContractReview, ContractSubjectReview, PaymentClauseReview, BreachClauseReview, GeneralReview
        from structured_service import StructuredReviewService
    except ImportError:
        from ContractAudit.structured_models import ComprehensiveContractReview, ContractSubjectReview, PaymentClauseReview, BreachClauseReview, GeneralReview
        from ContractAudit.structured_service import StructuredReviewService
    
    # 创建结构化审查服务实例
    structured_review_service = StructuredReviewService()
    print("✅ 结构化审查服务加载成功")
except ImportError as e:
    print(f"⚠️  结构化审查服务导入失败: {e}")
    # 创建备用结构化审查服务
    class SimpleStructuredReviewService:
        def create_comprehensive_prompt(self, contract_content: str) -> str:
            return f"请分析以下合同内容：\n{contract_content}"
        
        def parse_comprehensive_response(self, response_text: str):
            return {"status": "simplified", "content": response_text}
        
        def create_fallback_response(self, contract_content: str):
            return {"status": "fallback", "content": "简化分析结果"}
    
    structured_review_service = SimpleStructuredReviewService()
    print("⚠️  使用备用结构化审查服务")

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
            description="简化的合同审计对话系统",
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

# 全局异常处理器
@app.exception_handler(ContractAuditException)
async def contract_audit_exception_handler(request: Request, exc: ContractAuditException):
    """处理合同审计系统自定义异常"""
    print(f"===============================================================================")
    print(f"[EXCEPTION_HANDLER] 🚨 捕获到 ContractAuditException!")
    print(f"[EXCEPTION_HANDLER] ⏰ 时间戳: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[EXCEPTION_HANDLER] 🌐 请求路径: {request.url.path}")
    print(f"[EXCEPTION_HANDLER] 📝 错误类型: {exc.error_type}")
    print(f"[EXCEPTION_HANDLER] 💬 错误消息: {exc.message}")
    print(f"[EXCEPTION_HANDLER] 🔢 状态码: {exc.code}")
    print(f"[EXCEPTION_HANDLER] 📋 详细信息: {exc.details}")
    log_debug(f"[EXCEPTION_HANDLER] 捕获到 ContractAuditException: type={exc.error_type}, message={exc.message}, code={exc.code}, details={exc.details}")
    
    # 构建标准 JSON 响应
    response_content = {
        "code": exc.code,
        "message": exc.message,
        "error_type": exc.error_type,
        "details": exc.details,
        "success": False
    }
    
    print(f"[EXCEPTION_HANDLER] 📤 准备返回标准 JSON 响应:")
    print(f"[EXCEPTION_HANDLER] 📦 响应内容: {response_content}")
    print(f"[EXCEPTION_HANDLER] ✅ 返回 HTTP 状态码: 200 (业务错误码: {exc.code})")
    log_debug(f"[EXCEPTION_HANDLER] 返回标准 JSON 响应: {response_content}")
    print(f"===============================================================================")
    
    return JSONResponse(
        status_code=200,  # 返回200状态码，让前端能正常解析JSON
        content=response_content
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理所有未捕获的异常"""
    print(f"[EXCEPTION_HANDLER] 捕获到未处理异常:")
    print(f"  - 异常类型: {type(exc).__name__}")
    print(f"  - 异常消息: {str(exc)}")
    print(f"  - 请求路径: {request.url.path}")
    log_debug(f"[EXCEPTION_HANDLER] 捕获到未处理异常: type={type(exc).__name__}, message={str(exc)}, path={request.url.path}")
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"系统内部错误: {str(exc)}",
            "error_type": "INTERNAL_ERROR",
            "details": {
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            },
            "success": False
        }
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
    import time
    import json
    
    print(f"===============================================================================")
    print(f"[CHAT_CONFIRM] 🚀 收到 /chat/confirm 请求")
    print(f"[CHAT_CONFIRM] ⏰ 请求时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[CHAT_CONFIRM] 🌐 请求路径: {request.url.path}")
    print(f"[CHAT_CONFIRM] 📡 客户端地址: {request.client.host if request.client else 'Unknown'}")
    log_debug(f"[CHAT_CONFIRM] 收到 /chat/confirm 请求，时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    data = await request.json()
    session_id = data.get("session_id")
    message = data.get("message")
    auto_save = data.get("auto_save", False)
    user_id = data.get("user_id")
    project_name = data.get("project_name")
    
    print(f"[CHAT_CONFIRM] 📋 请求参数:")
    print(f"[CHAT_CONFIRM]   - session_id: {session_id}")
    print(f"[CHAT_CONFIRM]   - auto_save: {auto_save}")
    print(f"[CHAT_CONFIRM]   - user_id: {user_id}")
    print(f"[CHAT_CONFIRM]   - project_name: {project_name}")
    print(f"[CHAT_CONFIRM]   - message 长度: {len(message) if message else 0} 字符")
    log_debug(f"[CHAT_CONFIRM] 请求参数: session_id={session_id}, auto_save={auto_save}, user_id={user_id}")
    print(f"===============================================================================")

    # 初始化 rule_engine_result 变量（在 chat_confirm 函数作用域）
    rule_engine_result = None
    
    # 提前定义 rule/confirm 相关变量
    rule_engine_url = "http://172.18.53.39:8080/agent/python/rule/confirm"

    if not session_id or not message:
        raise ValidationException("session_id 和 message 必填")

    # 解析 message 字段
    try:
        message_data = dict_keys_to_snake(json.loads(message))
    except (json.JSONDecodeError, TypeError) as e:
        raise ValidationException("message 字段不是合法 JSON", field="message")

    # 深度去除 logicRuleList 字段（兼容嵌套和不同命名风格）
    def remove_logic_rule_list(obj):
        if isinstance(obj, dict):
            return {k: remove_logic_rule_list(v) for k, v in obj.items() if k not in ["logicRuleList", "logic_rule_list"]}
        elif isinstance(obj, list):
            return [remove_logic_rule_list(i) for i in obj]
        else:
            return obj
    message_data = remove_logic_rule_list(message_data)

    import httpx
    import asyncio
    import time
    from datetime import datetime, timedelta
    
    # 提前过滤规则：分离 censoredSearchEngine=1 的规则用于 rule/confirm
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
    
    # 过滤规则：只保留 censoredSearchEngine=0 的规则给 contract/view
    frontend_rules = message_data.get('reviewRules') or message_data.get('review_rules') or []
    filtered_rules = []
    censored_rules = []  # 用于后续 rule/confirm 处理
    
    print(f"[DEBUG] 开始过滤规则，前端规则数量: {len(frontend_rules)}")
    log_debug(f"[DEBUG] 开始过滤规则，前端规则数量: {len(frontend_rules)}")
    
    for rule in frontend_rules:
        # 递归查找 censoredSearchEngine 字段
        censored_search_engine, found_path = find_censored_search_engine(rule)
        rule_id = rule.get('ruleId') or rule.get('id') or 'unknown'
        
        print(f"[DEBUG] 规则 {rule_id} 的 censoredSearchEngine: {censored_search_engine} (路径: {found_path})")
        log_debug(f"[DEBUG] 规则 {rule_id} 的 censoredSearchEngine: {censored_search_engine} (路径: {found_path})")
        
        if censored_search_engine == 1:
            # censoredSearchEngine=1 的规则不传给 contract/view，只用于 rule/confirm
            censored_rules.append(rule)
            print(f"[DEBUG] 规则 {rule_id} censoredSearchEngine=1，跳过 contract/view，加入 rule/confirm 列表")
            log_debug(f"[DEBUG] 规则 {rule_id} censoredSearchEngine=1，跳过 contract/view，加入 rule/confirm 列表")
        else:
            # censoredSearchEngine=0 或未设置的规则传给 contract/view
            filtered_rules.append(rule)
            print(f"[DEBUG] 规则 {rule_id} censoredSearchEngine={censored_search_engine}，加入 contract/view 列表")
            log_debug(f"[DEBUG] 规则 {rule_id} censoredSearchEngine={censored_search_engine}，加入 contract/view 列表")
    
    print(f"[DEBUG] 过滤结果: contract/view 规则数量={len(filtered_rules)}, rule/confirm 规则数量={len(censored_rules)}")
    log_debug(f"[DEBUG] 过滤结果: contract/view 规则数量={len(filtered_rules)}, rule/confirm 规则数量={len(censored_rules)}")
    
    # 提前定义 contract_id 相关变量
    contract_id = (
        message_data.get("contractId") or 
        message_data.get("contract_id") or 
        "1234"  # 默认值
    )
    
    # 检查是否需要调用 rule/confirm 接口
    need_rule_confirm = len(censored_rules) > 0
    
    # 调试 contract_id 获取过程
    print(f"[DEBUG] contract_id 获取详情:")
    print(f"  - message_data.get('contractId'): {message_data.get('contractId')}")
    print(f"  - message_data.get('contract_id'): {message_data.get('contract_id')}")
    print(f"  - 最终 contract_id: {contract_id}")
    print(f"[DEBUG] rule/confirm 调用条件检查:")
    print(f"  - contract_id: {contract_id}")
    print(f"  - need_rule_confirm: {need_rule_confirm}")
    print(f"  - censored_rules 数量: {len(censored_rules)}")
    log_debug(f"[DEBUG] contract_id={contract_id}, need_rule_confirm={need_rule_confirm}, censored_rules_count={len(censored_rules)}")
    
    # 定义 validate_and_convert_condition_info 函数
    def validate_and_convert_condition_info(condition_list):
        """确保 conditionInfo 字段是字符串格式"""
        if not isinstance(condition_list, list):
            return condition_list
        
        processed_list = []
        for condition in condition_list:
            if isinstance(condition, dict) and 'conditionInfo' in condition:
                # 如果 conditionInfo 不是字符串，进行转换
                if not isinstance(condition['conditionInfo'], str):
                    try:
                        condition['conditionInfo'] = json.dumps(condition['conditionInfo'], ensure_ascii=False)
                    except:
                        condition['conditionInfo'] = str(condition['conditionInfo'])
            processed_list.append(condition)
        return processed_list
    
    import pytz

    # 获取上一个时间戳的时间（当前时间减去1秒）
    def get_previous_timestamp():
        """获取上一个时间戳的时间"""
        china_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(china_tz)
        previous_time = current_time - timedelta(seconds=1)
        return previous_time

    def clean_data_for_json(data):
        """清理数据，移除或转换datetime对象，确保可以JSON序列化"""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    # 将datetime转换为ISO格式字符串
                    cleaned[key] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    cleaned[key] = clean_data_for_json(value)
                else:
                    cleaned[key] = value
            return cleaned
        elif isinstance(data, list):
            return [clean_data_for_json(item) for item in data]
        else:
            return data

    async def event_stream():
        # 声明 nonlocal 变量，允许修改外层作用域的变量
        nonlocal rule_engine_result
        
        # 递归 riskLevel 转数字
        def risk_level_to_number(risk):
            if isinstance(risk, int):
                return risk
            if not risk:
                return -1
            if '高' in str(risk):
                return 3
            if '中' in str(risk):
                return 2
            if '低' in str(risk):
                return 1
            if '通过' in str(risk) or 'pass' in str(risk).lower():
                return 0
            return -1

        def convert_risk_level(obj):
            if isinstance(obj, dict):
                new_obj = {}
                for k, v in obj.items():
                    if k in ['riskLevel', 'risk_level']:
                        new_obj[k] = risk_level_to_number(v)
                    else:
                        new_obj[k] = convert_risk_level(v)
                return new_obj
            elif isinstance(obj, list):
                return [convert_risk_level(i) for i in obj]
            else:
                return obj

        # 先同步调用 doc_parser 接口
        doc_parser_url = "http://172.18.53.39:8888/api/v1/doc_parser"
        doc_url = message_data.get("url") or message_data.get("contract_url")
        doc_contract_id = message_data.get("contract_id")
        if doc_url and doc_contract_id:
            doc_parser_payload = {"url": doc_url, "contract_id": doc_contract_id}
            try:
                async with httpx.AsyncClient() as client:
                    await asyncio.wait_for(client.post(doc_parser_url, json=doc_parser_payload, timeout=30), timeout=60)
            except Exception as e:
                print(f"[WARN] 调用 doc_parser 失败: {e}")

        # contract_view接口
        url = "http://172.18.53.39:8888/api/v1/query/contract_view"
        default_contract_view_fields = {
            "reviewStage": "初审",
            "reviewList": 2,
            "reviewRules": [
                {
                    "id": 1,
                    "ruleName": "不得空白签字",
                    "type": 0,
                    "riskLevel": 2,
                    "riskAttributionId": 101,
                    "riskAttributionName": "法律部",
                    "censoredSearchEngine": 0,
                    "ruleGroupId": 10,
                    "ruleGroupName": "签署规范",
                    "includeRule": "签字页必须填写",
                     "exampleList": [
                        {
                            "contractContent": "string",
                            "judgmentResult": "string"
                        }
                    ],
                    "conditionalIdentifier": "",
                    "resultList": [

                    ]
                }
            ],
            "contractId": "1234",
        }
        
        # find_censored_search_engine 函数已移至 chat_confirm 函数外层
        
        # 规则过滤逻辑已移至 chat_confirm 函数外层
        
        contract_view_fields = list(default_contract_view_fields.keys())
        contract_view_payload = default_contract_view_fields.copy()
        
        # 使用过滤后的规则构建 contract_view 请求
        for k in contract_view_fields:
            if k == "reviewRules":
                # 使用过滤后的规则（只包含 censoredSearchEngine=0 的规则）
                value = [dict_keys_to_camel(rule) for rule in filtered_rules]
            elif k in message_data:
                value = message_data[k]
            elif camel_to_snake(k) in message_data:
                value = message_data[camel_to_snake(k)]
            else:
                value = contract_view_payload[k]
            contract_view_payload[k] = value

        # 特殊处理 contractId 字段
        if "contractId" in contract_view_payload:
            # 确保 contractId 字段存在且正确
            contract_id_value = (
                message_data.get("contractId") or 
                message_data.get("contract_id") or 
                contract_view_payload["contractId"]
            )
            contract_view_payload["contractId"] = contract_id_value
        else:
            # 如果没有 contractId，从 message_data 中获取
            contract_id_value = (
                message_data.get("contractId") or 
                message_data.get("contract_id") or 
                "1234"
            )
            contract_view_payload["contractId"] = contract_id_value

        # 修正 reviewList 字段为 int 类型
        if isinstance(contract_view_payload.get("reviewList"), list):
            if contract_view_payload["reviewList"]:
                contract_view_payload["reviewList"] = contract_view_payload["reviewList"][0]
            else:
                contract_view_payload["reviewList"] = 0  # 或根据实际业务设定默认值

        # 详细打印 contract_view 请求体
        import json
        print("=" * 80)
        print("🚀 CONTRACT_VIEW API 请求详情")
        print("=" * 80)
        print(f"📡 URL: {url}")
        print(f"📋 请求方法: POST")
        print(f"⏱️  超时时间: 60秒")
        print("-" * 80)
        print("📦 请求体 (JSON):")
        print(json.dumps(contract_view_payload, indent=2, ensure_ascii=False))
        print("-" * 80)
        print(f"📊 请求体大小: {len(json.dumps(contract_view_payload, ensure_ascii=False))} 字符")
        print(f"🔢 reviewRules 数量: {len(contract_view_payload.get('reviewRules', []))}")
        print(f"🆔 contractId: {contract_view_payload.get('contractId', 'N/A')}")
        print(f"📝 reviewStage: {contract_view_payload.get('reviewStage', 'N/A')}")
        print(f"📋 reviewList: {contract_view_payload.get('reviewList', 'N/A')}")
        print("=" * 80)
        
        # 同时记录到日志文件
        log_debug(f"[CONTRACT_VIEW_REQUEST] URL={url}")
        log_debug(f"[CONTRACT_VIEW_REQUEST] PAYLOAD={json.dumps(contract_view_payload, ensure_ascii=False)}")
        
        print(f"[LOG] contract_view 请求: url={url}, payload={contract_view_payload}")
        log_debug(f"[LOG] contract_view 请求: url={url}, payload={contract_view_payload}")
        contract_view_result = None
        contract_view_lines = []  # 新增：收集所有流式返回
        all_lines = []  # 新增：收集所有原始返回行
        try:
            async with httpx.AsyncClient() as client:
                import json  # 保证本作用域内有json
                async with client.stream("POST", url, json=contract_view_payload, timeout=60) as resp:
                    last_json = None
                    async for line in resp.aiter_lines():
                        all_lines.append(line)
                        if line.startswith("data: "):
                            json_str = line[6:]
                            print(f"[contract_view SSE] {json_str}")
                            contract_view_lines.append(json_str)
                            try:
                                last_json = json.loads(json_str)
                            except Exception as e:
                                print(f"[contract_view流式单行解析失败] error={e} line={json_str}")
                    if last_json is not None:
                        contract_view_result = last_json
                    elif contract_view_lines:
                        # 新增：如果最后一条解析失败，尝试用第一条
                        try:
                            contract_view_result = json.loads(contract_view_lines[0])
                        except Exception:
                            contract_view_result = {"error": "contract_view failed: no valid SSE JSON received"}
                    else:
                        # 没有任何 data: 行，尝试把所有行拼接为 JSON
                        try:
                            text = "".join(all_lines)
                            print(f"[DEBUG] contract_view resp text: {text}")
                            contract_view_result = json.loads(text)
                        except Exception as e:
                            contract_view_result = {"error": f"contract_view failed: {str(e)}"}
        except Exception as e:
            print(f"[contract_view调用失败] url={url} payload={contract_view_payload} error={e}")
            contract_view_result = {"error": f"contract_view failed: {str(e)}"}

        # 详细打印 contract_view 响应结果
        print("=" * 80)
        print("📥 CONTRACT_VIEW API 响应详情")
        print("=" * 80)
        if contract_view_result:
            if "error" in contract_view_result:
                print(f"❌ 响应状态: 错误")
                print(f"🚨 错误信息: {contract_view_result['error']}")
            else:
                print(f"✅ 响应状态: 成功")
                print(f"📊 响应体大小: {len(json.dumps(contract_view_result, ensure_ascii=False))} 字符")
                print(f"🔢 响应体键数量: {len(contract_view_result.keys())}")
                print(f"📋 响应体键列表: {list(contract_view_result.keys())}")
                print("-" * 80)
                print("📦 响应体 (JSON):")
                print(json.dumps(contract_view_result, indent=2, ensure_ascii=False))
        else:
            print("❌ 响应状态: 无响应")
        print("=" * 80)
        
        # 记录到日志文件
        log_debug(f"[CONTRACT_VIEW_RESPONSE] RESULT={json.dumps(contract_view_result, ensure_ascii=False)}")

        # ----------- 规则补全逻辑 begin -----------
        def extract_rules(source):
            if not source:
                return []
            return source.get("review_rules") or source.get("rules") or []

        def extract_rules_from_numbered_dict(data):
            rules = []
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict) and 'rule_id' in v and 'result_list' in v:
                        rule = {'rule_id': v['rule_id'], 'result_list': v['result_list'], 'status': v.get('status')}
                        rules.append(rule)
            return rules

        # 新增：递归提取所有 result_list
        def extract_all_result_lists(data):
            import json  # 保证作用域内有
            found = []
            if isinstance(data, dict):
                for v in data.values():
                    found.extend(extract_all_result_lists(v))
                if 'result_list' in data and 'rule_id' in data:
                    found.append({'rule_id': data['rule_id'], 'result_list': data['result_list'], 'status': data.get('status')})
            elif isinstance(data, list):
                for item in data:
                    found.extend(extract_all_result_lists(item))
            elif isinstance(data, str):
                # 新增：如果是字符串，尝试解析为 JSON
                try:
                    loaded = json.loads(data)
                    found.extend(extract_all_result_lists(loaded))
                except Exception:
                    pass
            return found

        print("=" * 80)
        print("🔍 规则提取详情")
        print("=" * 80)
        print(f"📊 contract_view_result 类型: {type(contract_view_result)}")
        print(f"📋 contract_view_result 键: {list(contract_view_result.keys()) if isinstance(contract_view_result, dict) else 'N/A'}")
        
        rules = extract_rules(contract_view_result)
        print(f"🔢 方法1提取规则数量: {len(rules)}")
        
        if not rules:
            rules = extract_rules_from_numbered_dict(contract_view_result)
            print(f"🔢 方法2提取规则数量: {len(rules)}")
        
        # 新增递归提取，合并所有 result_list
        all_result_list_rules = extract_all_result_lists(contract_view_result)
        print(f"🔢 递归提取规则数量: {len(all_result_list_rules)}")
        
        if all_result_list_rules:
            # 合并去重（以 rule_id 为主）
            exist_rule_ids = set(str(r.get('rule_id')) for r in rules)
            for r in all_result_list_rules:
                if str(r.get('rule_id')) not in exist_rule_ids:
                    rules.append(r)
        
        print(f"🔢 最终合并规则数量: {len(rules)}")
        if rules:
            print("📋 规则ID列表:")
            for i, rule in enumerate(rules[:5]):  # 只显示前5个
                rule_id = rule.get('rule_id') or rule.get('id') or rule.get('ruleId')
                rule_name = rule.get('rule_name') or rule.get('ruleName') or 'N/A'
                print(f"  {i+1}. ID: {rule_id}, 名称: {rule_name}")
            if len(rules) > 5:
                print(f"  ... 还有 {len(rules) - 5} 个规则")
        print("=" * 80)
        if not rules:
            rules = extract_rules(message_data)
        if not rules and isinstance(message_data.get("responsebody"), dict):
            rules = extract_rules(message_data["responsebody"])
        if rules:
            contract_view_result["review_rules"] = rules
        # ----------- 规则补全逻辑 end -----------

        # contract_view_result结构化
        def convert_numbered_dict_to_structured_result(data):
            if isinstance(data, dict) and all(k.isdigit() for k in data.keys()):
                rule_list = [v for v in data.values() if isinstance(v, dict)]
                total_issues = 0
                high_risk_items = 0
                medium_risk_items = 0
                low_risk_items = 0
                for rule in rule_list:
                    for r in rule.get('result_list', []):
                        # 兼容 risk_level 和 riskLevel
                        risk = r.get('riskLevel', r.get('risk_level', ''))
                        # riskLevel 直接转为数字
                        if '高' in risk:
                            r['riskLevel'] = 3
                            high_risk_items += 1
                        elif '中' in risk:
                            r['riskLevel'] = 2
                            medium_risk_items += 1
                        elif '低' in risk:
                            r['riskLevel'] = 1
                            low_risk_items += 1
                        elif '通过' in risk or 'pass' in risk.lower():
                            r['riskLevel'] = 0
                        else:
                            r['riskLevel'] = -1  # 未知
                if high_risk_items > 0:
                    overall_risk_level = 'high'
                elif medium_risk_items > 0:
                    overall_risk_level = 'medium'
                elif low_risk_items > 0:
                    overall_risk_level = 'low'
                else:
                    overall_risk_level = 'none'
                overall_summary = '\n'.join([r.get('explanation', '') for rule in rule_list for r in rule.get('result_list', []) if r.get('explanation')])
                return {
                    'rules': rule_list,
                    'total_issues': total_issues,
                    'high_risk_items': high_risk_items,
                    'medium_risk_items': medium_risk_items,
                    'low_risk_items': low_risk_items,
                    'overall_risk_level': overall_risk_level,
                    'overall_summary': overall_summary,
                }
            return data

        contract_view_result_for_save = convert_numbered_dict_to_structured_result(contract_view_result)

        # rule/confirm 调用逻辑已移至 chat_confirm 函数外层



        # 自动保存所有规则到 confirm_review_rule_result
        from ContractAudit.models import create_confirm_review_rule_result
        from ContractAudit.config import get_session
        db = next(get_session())
        rule_save_results = []
        raw_rule_map = {}
        for raw_rule in message_data.get('review_rules', []):
            raw_rule_map[str(raw_rule.get('id') or raw_rule.get('rule_id'))] = raw_rule

        processed_count = 0
        total_rules = len(rules)
        all_completed_rules = []
        def ensure_str_list(val):
            if val is None:
                return []
            if isinstance(val, list):
                return [str(v) for v in val if v is not None and str(v).strip() != '']
            if isinstance(val, str):
                return [val] if val.strip() else []
            return [str(val)]
        
        def handle_rule_confirm_fallback(completed_rule, rule_id, error_info=None):
            """处理 rule/confirm 兜底逻辑"""
            print(f"[FALLBACK] 规则 {rule_id} 使用兜底处理")
            if error_info:
                print(f"[FALLBACK] 错误信息: {error_info}")
            
            # 兜底策略：根据匹配内容判断，而不是直接设置为失败
            matched_content = completed_rule.get('matched_content', '')
            if not matched_content or matched_content.strip() == "":
                # 没有匹配内容，设置为通过
                completed_rule['rule_confirm_result'] = True
                completed_rule['review_result'] = "pass"
                print(f"[FALLBACK] 规则 {rule_id} 没有匹配内容，设置为通过")
            else:
                # 有匹配内容，设置为不通过
                completed_rule['rule_confirm_result'] = False
                completed_rule['review_result'] = "done"
                print(f"[FALLBACK] 规则 {rule_id} 有匹配内容，设置为不通过")
            
            if error_info:
                completed_rule['rule_confirm_error'] = error_info
            
            # 记录兜底处理日志
            try:
                log_debug(f"[FALLBACK] 规则 {rule_id} 使用兜底处理，错误: {error_info}, 结果: {completed_rule['review_result']}")
            except Exception as e:
                print(f"[FALLBACK] 记录日志失败: {e}")
            
            return completed_rule
        def merge_rule_fields(rule, fields):
            """
            合并主规则和所有result_list子项中指定字段的内容为字符串数组
            """
            merged = {k: [] for k in fields}
            # 主规则
            for k in fields:
                merged[k].extend(ensure_str_list(rule.get(k)))
            # result_list子项
            result_list = rule.get("result_list", [])
            for item in result_list:
                for k in fields:
                    merged[k].extend(ensure_str_list(item.get(k)))
            # 去除空字符串
            for k in fields:
                merged[k] = [s for s in merged[k] if s is not None and str(s).strip() != '']
            return merged
        def merge_fields_in_rule(rule, fields):
            """
            合并主规则和所有result_list子项中指定字段的内容为字符串数组，赋值回原字段，其它字段不变
            """
            for k in fields:
                merged = []
                # 主规则
                merged.extend(ensure_str_list(rule.get(k)))
                # result_list子项
                result_list = rule.get("result_list", [])
                for item in result_list:
                    merged.extend(ensure_str_list(item.get(k)))
                # 去除空字符串
                merged = [s for s in merged if s is not None and str(s).strip() != '']
                if merged:
                    rule[k] = merged
        # 在推送每条规则前，合并四个字段内容
        merge_keys = ["issues", "suggestions", "analysis", "matched_content"]
        # 只以前端传入的规则为主，保证每个 rule-id 只返回一条
        frontend_rules = message_data.get('reviewRules') or message_data.get('review_rules') or []
        all_completed_rules = []
        processed_count = 0
        total_rules = len(frontend_rules)
        
        # 获取上一个时间戳的时间
        previous_timestamp = get_previous_timestamp()
        print(f"[DEBUG] 使用上一个时间戳: {previous_timestamp}")
        
        for idx, fr in enumerate(frontend_rules):
            rule_id = fr.get('ruleId') or fr.get('id')
            # 在后端规则列表中查找对应 rule-id
            matched_rule = None
            for rule in rules:
                rid = rule.get('ruleId') or rule.get('id') or rule.get('rule_id')
                if str(rid) == str(rule_id):
                    matched_rule = rule
                    break
            if not matched_rule:
                matched_rule = fr  # 如果后端没查到，直接用前端的
            # 复制一份，避免影响原数据
            completed_rule = dict(matched_rule)
            
            # 检查是否需要处理 rule/confirm 响应结果
            # 获取 rule_id - 保持与之前获取的 rule_id 一致
            # rule_id = fr.get('ruleId') or fr.get('id') or idx + 1  # 注释掉这行，避免重新赋值
            
            # 检查当前规则是否在 censored_rules 列表中（censoredSearchEngine=1）
            current_rule_censored = fr in censored_rules
            if current_rule_censored:
                print(f"[DEBUG] 规则 {rule_id} 在 censored_rules 列表中，需要处理 rule/confirm")
                print(f"[DEBUG] 开始处理 rule/confirm 响应，规则ID: {rule_id}")
                log_debug(f"[DEBUG] 开始处理 rule/confirm 响应，规则ID: {rule_id}")
            
            if current_rule_censored and rule_engine_result and isinstance(rule_engine_result, dict):
                # 检查是否有错误信息
                has_error = rule_engine_result.get('error') or rule_engine_result.get('fallback')
                if has_error:
                    error_info = rule_engine_result.get('error', 'Unknown error')
                    completed_rule = handle_rule_confirm_fallback(completed_rule, rule_id, error_info)
                else:
                    # 从 rule/confirm 响应中获取布尔值结果
                    # 注意：rule/confirm 返回的是批量响应格式，需要根据当前规则ID查找对应结果
                    rule_confirm_success = None
                
                # 适配 Java BaseResponse 格式的响应解析逻辑
                rule_confirm_success = None
                
                # 检查是否是 Java BaseResponse 格式
                if isinstance(rule_engine_result, dict):
                    # 检查错误码：14000000 表示失败，20000000 表示成功
                    error_code = rule_engine_result.get('code') or rule_engine_result.get('errorCode')
                    
                    if error_code == 14000000:
                        # 失败情况 - 但这里不应该执行到，因为已经在流开始前检查过了
                        print(f"[WARN] 规则 {rule_id} 遇到错误码 14000000，但应该在流开始前就被处理")
                        rule_confirm_success = False
                    elif error_code == 20000000 or error_code == 10000000:  # 添加对 10000000 的支持
                        # 成功情况，需要从 data 字段提取批量结果
                        data = rule_engine_result.get('data')
                        if isinstance(data, list):
                            # 批量响应格式：在 data 数组中查找当前规则的结果
                            print(f"[DEBUG] 处理批量响应，当前规则ID: {rule_id}")
                            print(f"[DEBUG] 批量响应数据: {data}")
                            
                            # 在批量结果中查找当前规则的结果
                            current_rule_result = None
                            for result_item in data:
                                result_rule_id = result_item.get('ruleId') or result_item.get('rule_id')
                                if str(result_rule_id) == str(rule_id):
                                    current_rule_result = result_item
                                    break
                            
                            if current_rule_result:
                                # 找到当前规则的结果
                                judge_result = current_rule_result.get('result')
                                if isinstance(judge_result, bool):
                                    rule_confirm_success = judge_result
                                else:
                                    # 如果不是布尔值，尝试转换
                                    rule_confirm_success = bool(judge_result) if judge_result is not None else None
                                
                                # 提取 verbatimTextList 和 reviseOpinion 字段
                                verbatim_text_list = current_rule_result.get('verbatimTextList', [])
                                revise_opinion = current_rule_result.get('reviseOpinion')
                                
                                # 将提取的字段添加到 completed_rule 中，确保与contract/review格式一致
                                if verbatim_text_list:
                                    completed_rule['verbatimTextList'] = verbatim_text_list
                                    # 存储到 matched_content 字段，与contract/review格式保持一致
                                    if isinstance(verbatim_text_list, list):
                                        completed_rule['matched_content'] = "；".join([str(item) for item in verbatim_text_list if item])
                                    else:
                                        completed_rule['matched_content'] = str(verbatim_text_list)
                                else:
                                    # 如果没有verbatimTextList，确保matched_content字段存在
                                    completed_rule['matched_content'] = completed_rule.get('matched_content', "")
                                
                                # 存储 reviseOpinion 字段
                                completed_rule['reviseOpinion'] = revise_opinion
                                
                                # 处理 suggestions 字段，与contract/review格式保持一致
                                if revise_opinion is not None and str(revise_opinion).strip():
                                    completed_rule['suggestions'] = str(revise_opinion)
                                else:
                                    # 如果没有reviseOpinion，使用默认值或保持原有值
                                    completed_rule['suggestions'] = completed_rule.get('suggestions', "")
                                
                                # 确保 analysis 字段存在，与contract/review格式保持一致
                                if 'analysis' not in completed_rule:
                                    completed_rule['analysis'] = ""
                                
                                # 确保 issues 字段存在，与contract/review格式保持一致
                                if 'issues' not in completed_rule:
                                    completed_rule['issues'] = []
                                
                                # 确保 resultList 字段存在，与contract/review格式保持一致
                                if 'resultList' not in completed_rule:
                                    completed_rule['resultList'] = []
                                
                                # 构建 resultList，与contract/review格式保持一致
                                result_list = []
                                result_item = {}
                                
                                if completed_rule.get('suggestions'):
                                    result_item["suggestions"] = str(completed_rule['suggestions'])
                                
                                if completed_rule.get('matched_content'):
                                    result_item["matched_content"] = str(completed_rule['matched_content'])
                                
                                if result_item:
                                    result_list.append(result_item)
                                
                                completed_rule['resultList'] = result_list
                                
                                print(f"[DEBUG] 找到规则 {rule_id} 的结果: {judge_result} -> {rule_confirm_success}")
                                print(f"[DEBUG] 提取的 verbatimTextList: {verbatim_text_list}")
                                print(f"[DEBUG] 提取的 reviseOpinion: {revise_opinion}")
                                print(f"[DEBUG] 存储到 matched_content: {completed_rule.get('matched_content')}")
                                print(f"[DEBUG] 存储到 suggestions: {completed_rule.get('suggestions')}")
                                print(f"[DEBUG] 存储到 reviseOpinion: {completed_rule.get('reviseOpinion')}")
                                print(f"[DEBUG] 存储前 reviseOpinion 类型: {type(revise_opinion)}")
                                print(f"[DEBUG] 存储后 reviseOpinion 类型: {type(completed_rule.get('reviseOpinion'))}")
                            else:
                                # 没有找到当前规则的结果，使用兜底处理而不是直接失败
                                rule_confirm_success = None
                                print(f"[DEBUG] 未找到规则 {rule_id} 的结果，使用兜底处理")
                        elif isinstance(data, dict):
                            # 单个结果格式：从 JudgeResultDto 中提取 result 字段
                            judge_result = data.get('result')
                            if isinstance(judge_result, bool):
                                rule_confirm_success = judge_result
                            else:
                                # 如果不是布尔值，尝试转换
                                rule_confirm_success = bool(judge_result) if judge_result is not None else None
                        else:
                            # data 不是列表或字典，尝试直接使用
                            rule_confirm_success = bool(data) if data is not None else None
                        print(f"[DEBUG] rule/confirm 返回成功码: {error_code}, data: {data}, result: {rule_confirm_success}")
                    else:
                        # 其他错误码或未知格式 - 但这里不应该执行到，因为已经在流开始前检查过了
                        print(f"[WARN] 规则 {rule_id} 遇到未知错误码 {error_code}，但应该在流开始前就被处理")
                        rule_confirm_success = None
                else:
                    # 非字典格式 - 但这里不应该执行到，因为已经在流开始前检查过了
                    print(f"[WARN] 规则 {rule_id} 遇到格式异常，但应该在流开始前就被处理")
                    rule_confirm_success = None
                
                # 如果代码执行到这里，说明 rule/confirm 调用成功且返回了有效结果
                print(f"[DEBUG] rule/confirm 处理成功，规则 {rule_id} 结果: {rule_confirm_success}")
                print(f"[DEBUG] rule/confirm 原始响应: {rule_engine_result}")
                print(f"[DEBUG] 规则 {rule_id} rule/confirm 处理完成")
                log_debug(f"[DEBUG] 规则 {rule_id} rule/confirm 处理完成，结果: {rule_confirm_success}")
                
                # 根据布尔值设置 review_result：true -> "pass", false -> "done"
                if rule_confirm_success is True:
                    completed_rule['review_result'] = "pass"
                    completed_rule['rule_confirm_result'] = True
                    print(f"[DEBUG] 规则 {rule_id} 通过 rule/confirm 验证，设置 review_result=pass")
                elif rule_confirm_success is False:
                    completed_rule['review_result'] = "done"
                    completed_rule['rule_confirm_result'] = False
                    print(f"[DEBUG] 规则 {rule_id} 未通过 rule/confirm 验证，设置 review_result=done")
                else:
                    # 如果结果不是明确的布尔值，使用兜底处理
                    print(f"[WARN] 规则 {rule_id} rule/confirm 结果不明确: {rule_confirm_success}")
                    error_info = "规则引擎结果不明确或调用失败"
                    completed_rule = handle_rule_confirm_fallback(completed_rule, rule_id, error_info)
            else:
                # 如果当前规则需要 rule/confirm 处理但没有结果，使用兜底处理
                if current_rule_censored:
                    if not rule_engine_result or not isinstance(rule_engine_result, dict):
                        print(f"[WARN] 规则 {rule_id} 需要 rule/confirm 处理但结果异常，使用兜底处理")
                        error_info = f"rule/confirm 结果异常: {type(rule_engine_result).__name__}"
                        completed_rule = handle_rule_confirm_fallback(completed_rule, rule_id, error_info)
                else:
                    print(f"[DEBUG] 无需处理 rule/confirm 响应: current_rule_censored={current_rule_censored}, rule_engine_result={rule_engine_result}")
                    try:
                        log_debug(f"[DEBUG] 无需处理 rule/confirm 响应: current_rule_censored={current_rule_censored}, rule_engine_result={rule_engine_result}")
                    except Exception as e:
                        print(f"[LOG_DEBUG] 无需处理 rule/confirm 响应: current_rule_censored={current_rule_censored}, rule_engine_result={rule_engine_result}")
                        print(f"[LOG_DEBUG] 写入日志失败: {e}")
            # 字段提取辅助函数
            def get_first(*args, default=None):
                for arg in args:
                    if arg is not None:
                        return arg
                return default
            def join_result_list_field(rule, field):
                if 'result_list' in rule and isinstance(rule['result_list'], list):
                    return "；".join([str(item.get(field, "")) for item in rule['result_list'] if item.get(field)])
                return ""
            # 按表结构字段优先级赋值
            completed_rule['contract_id'] = get_first(
                fr.get('contractId'), fr.get('contract_id'),
                message_data.get('contractId'), message_data.get('contract_id'),
                matched_rule.get('contractId') or matched_rule.get('contract_id'),
                "1234"  # 默认值，避免从 contract_view_result 获取失败
            )
            # 只有在没有 rule/confirm 结果时才设置这些字段，避免覆盖 rule/confirm 的结果
            if 'rule_confirm_result' not in completed_rule:
                completed_rule['matched_content'] = get_first(
                    matched_rule.get('matched_content'), matched_rule.get('matchedContent'),
                    join_result_list_field(matched_rule, 'matched_content'),
                    fr.get('matchedContent'), fr.get('matched_content'),
                    join_result_list_field(fr, 'matched_content'),
                    ""
                )
                completed_rule['issues'] = get_first(
                    matched_rule.get('issues'),
                    join_result_list_field(matched_rule, 'issues'),
                    fr.get('issues'),
                    join_result_list_field(fr, 'issues'),
                    []
                )
                completed_rule['suggestions'] = get_first(
                    matched_rule.get('suggestions'),
                    join_result_list_field(matched_rule, 'suggestions'),
                    fr.get('suggestions'),
                    join_result_list_field(fr, 'suggestions'),
                    []
                )
            else:
                # 已经有 rule/confirm 结果，保持现有值，只设置缺失的字段
                if 'matched_content' not in completed_rule:
                    completed_rule['matched_content'] = get_first(
                        matched_rule.get('matched_content'), matched_rule.get('matchedContent'),
                        join_result_list_field(matched_rule, 'matched_content'),
                        fr.get('matchedContent'), fr.get('matched_content'),
                        join_result_list_field(fr, 'matched_content'),
                        ""
                    )
                if 'issues' not in completed_rule:
                    completed_rule['issues'] = get_first(
                        matched_rule.get('issues'),
                        join_result_list_field(matched_rule, 'issues'),
                        fr.get('issues'),
                        join_result_list_field(fr, 'issues'),
                        []
                    )
                if 'suggestions' not in completed_rule:
                    completed_rule['suggestions'] = get_first(
                        matched_rule.get('suggestions'),
                        join_result_list_field(matched_rule, 'suggestions'),
                        fr.get('suggestions'),
                        join_result_list_field(fr, 'suggestions'),
                        []
                    )
            # 其它字段也加 fr 兜底
            risk_level_value = get_first(
                matched_rule.get('risk_level'), matched_rule.get('riskLevel'),
                fr.get('riskLevel'), fr.get('risk_level'),
                "none"
            )
            # 确保 risk_level 是数字类型
            if isinstance(risk_level_value, str):
                completed_rule['risk_level'] = risk_level_to_number(risk_level_value)
            else:
                completed_rule['risk_level'] = risk_level_value if risk_level_value is not None else -1
            completed_rule['rule_group_id'] = get_first(
                matched_rule.get('rule_group_id'), fr.get('ruleGroupId'), fr.get('rule_group_id')
            )
            completed_rule['rule_group_name'] = get_first(
                matched_rule.get('rule_group_name'), fr.get('ruleGroupName'), fr.get('rule_group_name')
            )
            completed_rule['risk_attribution_id'] = get_first(
                matched_rule.get('risk_attribution_id'), fr.get('riskAttributionId'), fr.get('risk_attribution_id')
            )
            completed_rule['risk_attribution_name'] = get_first(
                matched_rule.get('risk_attribution_name'), fr.get('riskAttributionName'), fr.get('risk_attribution_name')
            )
            completed_rule['rule_id'] = get_first(
                fr.get('ruleId'), fr.get('id'),
                matched_rule.get('rule_id'), matched_rule.get('id'),
                idx + 1
            )
            completed_rule['rule_name'] = get_first(
                fr.get('ruleName'), fr.get('rule_name'),
                matched_rule.get('ruleName'), matched_rule.get('rule_name'),
                str(completed_rule['rule_id'])
            )
            completed_rule['rule_index'] = get_first(
                fr.get('ruleIndex'), fr.get('rule_index'),
                matched_rule.get('ruleIndex'), matched_rule.get('rule_index'),
                idx
            )
            # 根据 match_content 是否为空确定审查结果：通过传"pass"，不通过传"done"
            def determine_review_result(match_content):
                if not match_content or match_content.strip() == "":
                    return "pass"  # 没有匹配内容，通过
                else:
                    return "done"  # 有匹配内容，不通过
            
            # 获取匹配内容
            match_content_value = completed_rule.get('matched_content', "")
            if not match_content_value:
                # 如果没有设置匹配内容，尝试从其他地方获取
                match_content_value = get_first(
                    matched_rule.get('matched_content'), matched_rule.get('matchedContent'),
                    join_result_list_field(matched_rule, 'matched_content'),
                    fr.get('matchedContent'), fr.get('matched_content'),
                    join_result_list_field(fr, 'matched_content'),
                    ""
                )
            
            # 确定审查结果 - 只有在没有 rule/confirm 结果时才使用默认逻辑
            if 'review_result' not in completed_rule:
                completed_rule['review_result'] = determine_review_result(match_content_value)
                print(f"[DEBUG] 规则 {rule_id} 没有 review_result，使用默认逻辑: {completed_rule['review_result']}")
            # 新增：如果已经有 rule/confirm 结果，不要被后续逻辑覆盖
            elif 'rule_confirm_result' in completed_rule and completed_rule.get('review_result'):
                # 已经有 rule/confirm 结果，保持原有结果
                print(f"[DEBUG] 规则 {rule_id} 已有 rule/confirm 结果，保持 review_result={completed_rule['review_result']}")
                try:
                    log_debug(f"[DEBUG] 规则 {rule_id} 已有 rule/confirm 结果，保持 review_result={completed_rule['review_result']}")
                except Exception as e:
                    print(f"[LOG_DEBUG] 规则 {rule_id} 已有 rule/confirm 结果，保持 review_result={completed_rule['review_result']}")
                    print(f"[LOG_DEBUG] 写入日志失败: {e}")
            else:
                # 没有 rule/confirm 结果，使用默认逻辑
                completed_rule['review_result'] = determine_review_result(match_content_value)
                print(f"[DEBUG] 规则 {rule_id} 使用默认逻辑设置 review_result: {completed_rule['review_result']}")
            completed_rule['analysis'] = get_first(
                matched_rule.get('analysis'), matched_rule.get('explanation'),
                join_result_list_field(matched_rule, 'explanation'),
                fr.get('analysis'), fr.get('explanation'),
                join_result_list_field(fr, 'explanation'),
                ""
            )
            completed_rule['confidence_score'] = get_first(
                matched_rule.get('confidence_score'), fr.get('confidence_score'), 50
            )
            # 存储到数据库，直接用 completed_rule
            completed_rule['session_id'] = session_id
            completed_rule['rule_name'] = (
                completed_rule.get('rule_name')
                or completed_rule.get('ruleName')
                or str(completed_rule.get('rule_id') or completed_rule.get('id') or '')
            )
            def safe_list(val):
                if val == '' or val is None:
                    return []
                if isinstance(val, list):
                    return val
                try:
                    import json
                    v = json.loads(val)
                    if isinstance(v, list):
                        return v
                    return [v]
                except Exception:
                    return []
            # 兼容所有应为 list 的字段，并保证存入数据库前为可解析的JSON字符串
            import json
            for key in ["issues", "suggestions", "analysis", "matched_content", "reviseOpinion", "verbatimTextList"]:
                val = completed_rule.get(key)
                if val is None:
                    completed_rule[key] = json.dumps([], ensure_ascii=False)
                elif isinstance(val, (list, dict)):
                    completed_rule[key] = json.dumps(val, ensure_ascii=False)
                elif isinstance(val, str):
                    try:
                        # 尝试解析为JSON，能解析则标准化
                        loaded = json.loads(val)
                        completed_rule[key] = json.dumps(loaded, ensure_ascii=False)
                    except Exception:
                        # 不能解析就原样存储
                        completed_rule[key] = val
            
            # 添加自定义的创建时间（使用上一个时间戳）
            completed_rule['created_at'] = previous_timestamp
            
            # 添加调试日志，确保 rule/confirm 结果正确传递
            print(f"[DEBUG] 准备存储规则到数据库:")
            print(f"  - rule_id: {completed_rule.get('rule_id')}")
            print(f"  - rule_name: {completed_rule.get('rule_name')}")
            print(f"  - review_result: {completed_rule.get('review_result')}")
            print(f"  - rule_confirm_result: {completed_rule.get('rule_confirm_result', 'N/A')}")
            print(f"  - session_id: {completed_rule.get('session_id')}")
            print(f"  - contract_id: {completed_rule.get('contract_id')}")
            print(f"  - reviseOpinion: {completed_rule.get('reviseOpinion')}")
            print(f"  - suggestions: {completed_rule.get('suggestions')}")
            print(f"  - matched_content: {completed_rule.get('matched_content')}")
            try:
                log_debug(f"[DEBUG] 准备存储规则到数据库: rule_id={completed_rule.get('rule_id')}, review_result={completed_rule.get('review_result')}, rule_confirm_result={completed_rule.get('rule_confirm_result', 'N/A')}")
            except Exception as e:
                print(f"[LOG_DEBUG] 准备存储规则到数据库: rule_id={completed_rule.get('rule_id')}, review_result={completed_rule.get('review_result')}, rule_confirm_result={completed_rule.get('rule_confirm_result', 'N/A')}")
                print(f"[LOG_DEBUG] 写入日志失败: {e}")
            
            try:
                result = create_confirm_review_rule_result(db, completed_rule)
                print(f"[DEBUG] 规则存储成功: ID={result.id}, review_result={result.review_result}")
                try:
                    log_debug(f"[DEBUG] 规则存储成功: ID={result.id}, review_result={result.review_result}")
                except Exception as e:
                    print(f"[LOG_DEBUG] 规则存储成功: ID={result.id}, review_result={result.review_result}")
                    print(f"[LOG_DEBUG] 写入日志失败: {e}")
            except Exception as e:
                import traceback
                print(f"[ERROR] 保存规则失败: {e}")
                print(traceback.format_exc())
                try:
                    log_debug(f"[ERROR] 保存规则失败: {e}")
                except Exception as log_e:
                    print(f"[LOG_DEBUG] 保存规则失败: {e}")
                    print(f"[LOG_DEBUG] 写入日志失败: {log_e}")
            processed_count += 1
            event_data = {
                "event": "rule_completed",
                "timestamp": time.time(),
                "data": {
                    "session_id": session_id,
                    "status": "rule_completed",
                    "completed_rule": dict_keys_to_camel(convert_risk_level(completed_rule)),
                    "processed_count": processed_count,
                    "total_rules": total_rules,
                    "message": f"规则 {completed_rule.get('ruleName') or completed_rule.get('rule_name') or rule_id} 审查完成"
                }
            }
            
            # 清理数据，确保可以JSON序列化
            event_data = clean_data_for_json(event_data)
            
            # SSE发送前sleep 1秒
            await asyncio.sleep(1)
            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
            all_completed_rules.append(completed_rule)
        # 最终收尾事件
        def process_rule_for_frontend(rule, fr):
            # 保持原有字段
            rule = dict_keys_to_camel(convert_risk_level(rule))
            merge_fields_in_rule(rule, ["issues", "analysis"])
            
            # 字段补全/重命名/增加，确保与contract/review格式一致
            rule['ruleGroupId'] = fr.get('ruleGroupId') or fr.get('rule_group_id')
            rule['ruleGroupName'] = fr.get('ruleGroupName') or fr.get('rule_group_name')
            rule['riskAttributionId'] = (
                fr.get('riskAttributionId') or fr.get('risk_attribution_id') or
                fr.get('riskAttribution') or fr.get('risk_attribution')
            )
            rule['riskAttributionName'] = (
                fr.get('riskAttributionName') or fr.get('risk_attribution_name') or
                fr.get('riskName') or fr.get('risk_name')
            )
            
            # 确保 riskLevel 是数字类型
            risk_level_value = fr.get('riskLevel') or fr.get('risk_level')
            if isinstance(risk_level_value, str):
                rule['riskLevel'] = risk_level_to_number(risk_level_value)
            else:
                rule['riskLevel'] = risk_level_value if risk_level_value is not None else -1
            
            rule['ruleName'] = fr.get('ruleName') or fr.get('rule_name')
            
            # 设置 reviewResult 字段：优先使用 rule/confirm 的结果，否则根据匹配内容判断
            def determine_review_result_for_frontend(rule_data):
                # 优先使用 rule/confirm 的结果（检查多种可能的字段名）
                if 'review_result' in rule_data:
                    return rule_data['review_result']
                elif 'reviewResult' in rule_data:
                    return rule_data['reviewResult']
                
                # 否则根据匹配内容判断
                match_content_value = rule_data.get('matchedContent') or rule_data.get('matched_content') or ""
                if not match_content_value or match_content_value.strip() == "":
                    return "pass"  # 没有匹配内容，通过
                else:
                    return "done"  # 有匹配内容，不通过
            
            # 添加调试日志，检查 rule 中是否包含 review_result 字段
            print(f"[DEBUG] process_rule_for_frontend: rule_id={rule.get('ruleId') or rule.get('id')}, review_result字段存在={('review_result' in rule)}, reviewResult字段存在={('reviewResult' in rule)}")
            if 'review_result' in rule:
                print(f"[DEBUG] review_result 值: {rule['review_result']}")
            if 'reviewResult' in rule:
                print(f"[DEBUG] reviewResult 值: {rule['reviewResult']}")
            
            # 在设置 reviewResult 之前记录当前状态
            print(f"[DEBUG] 设置 reviewResult 之前的状态: rule_id={rule.get('ruleId') or rule.get('id')}")
            
            rule['reviewResult'] = determine_review_result_for_frontend(rule)
            
            # 在设置 reviewResult 之后记录最终状态
            print(f"[DEBUG] 设置 reviewResult 之后的状态: rule_id={rule.get('ruleId') or rule.get('id')}, reviewResult={rule['reviewResult']}")
            
            # 前端可以通过 reviewResult 字段判断 rule/confirm 的结果
            # reviewResult: "pass" 表示通过, "done" 表示不通过
            
            # 确保所有contract/review格式的字段都存在
            if 'matchedContent' not in rule:
                rule['matchedContent'] = rule.get('matched_content', "")
            
            if 'suggestions' not in rule:
                rule['suggestions'] = ""
            
            if 'analysis' not in rule:
                rule['analysis'] = ""
            
            if 'issues' not in rule:
                rule['issues'] = []
            
            # 构建 resultList 字段，与contract/review格式保持一致
            result_list = []
            result_item = {}
            
            if rule.get('suggestions'):
                result_item["suggestions"] = str(rule['suggestions'])
            
            if rule.get('matchedContent'):
                result_item["matched_content"] = str(rule['matchedContent'])
            
            # 如果有数据，添加到 resultList
            if result_item:
                result_list.append(result_item)
            
            rule['resultList'] = result_list
            
            # 兼容 overallExplanation/overallResult
            rule['overallExplanation'] = rule.get('overallExplanation') or rule.get('overall_explanation', "")
            rule['overallResult'] = rule.get('overallResult') or rule.get('overall_result', "")
            
            # 确保所有contract/review格式的字段都存在，与contract/review格式完全一致
            required_fields = {
                'ruleId': rule.get('ruleId') or rule.get('id'),
                'ruleName': rule.get('ruleName'),
                'reviewResult': rule.get('reviewResult'),
                'riskLevel': rule.get('riskLevel'),
                'matchedContent': rule.get('matchedContent'),
                'suggestions': rule.get('suggestions'),
                'analysis': rule.get('analysis'),
                'issues': rule.get('issues'),
                'resultList': rule.get('resultList'),
                'ruleGroupId': rule.get('ruleGroupId'),
                'ruleGroupName': rule.get('ruleGroupName'),
                'riskAttributionId': rule.get('riskAttributionId'),
                'riskAttributionName': rule.get('riskAttributionName'),
                'overallExplanation': rule.get('overallExplanation'),
                'overallResult': rule.get('overallResult')
            }
            
            # 更新rule，确保所有字段都存在
            for field, value in required_fields.items():
                if value is not None:
                    rule[field] = value
            
            return rule
        final_data = {
            "code": 0,
            "data": [process_rule_for_frontend(r, fr) for r, fr in zip(all_completed_rules, frontend_rules)],
            "maxPage": 1,
            "message": "全部规则审查完成",
            "rule_confirm_status": {
                "called": need_rule_confirm,
                "censored_rules_count": len(censored_rules),
                "censored_rule_ids": [rule.get('ruleId') or rule.get('id') for rule in censored_rules],
                "rule_confirm_result": rule_engine_result if need_rule_confirm else None
            }
        }
        event_data = {
            "event": "complete",
            "timestamp": time.time(),
            "data": final_data
        }
        
        # 清理数据，确保可以JSON序列化
        event_data = clean_data_for_json(event_data)
        
        # 🔥🔥🔥 DEBUG: event_stream 函数结束前检查 rule_engine_result
        print(f"🔥🔥🔥 DEBUG: event_stream 结束，rule_engine_result = {rule_engine_result} 🔥🔥🔥")
        
        # 最终事件发送前也sleep 1秒
        await asyncio.sleep(1)
        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

    # ===============================================================================
    # 🚨 关键修复：在流式响应开始前调用 rule/confirm 并检查结果
    # ===============================================================================
    
    # 执行 rule/confirm 调用（从 event_stream 移出）
    if contract_id and need_rule_confirm:
        # 构建标准格式的 rule/confirm 请求体
        review_rule_dto_list = []
        # 使用前端传入的规则，而不是 contract_view 返回的规则
        for rule in censored_rules:
            rule_id = rule.get('ruleId') or rule.get('id') or rule.get('rule_id')
            if rule_id:
                # 先处理 conditionInfo 字段，确保它是字符串格式
                if 'conditionList' in rule:
                    rule['conditionList'] = validate_and_convert_condition_info(rule['conditionList'])
                elif 'condition_list' in rule:
                    rule['condition_list'] = validate_and_convert_condition_info(rule['condition_list'])
                
                # 再对整个 rule 对象进行驼峰转换
                rule_camel = dict_keys_to_camel(rule)
                
                # 构建标准格式的规则DTO，使用转换后的规则数据
                rule_dto = {
                    "id": int(rule_id) if isinstance(rule_id, (int, str)) else rule_id,
                    "ruleName": rule_camel.get('ruleName') or f"规则{rule_id}",
                    "type": rule_camel.get('type', 0),
                    "riskLevel": rule_camel.get('riskLevel', 1),
                    "riskAttributionId": rule_camel.get('riskAttributionId', 1),
                    "riskAttributionName": rule_camel.get('riskAttributionName', "默认风险归属"),
                    "censoredSearchEngine": rule_camel.get('censoredSearchEngine', 0),
                    "ruleGroupId": rule_camel.get('ruleGroupId', 1),
                    "ruleGroupName": rule_camel.get('ruleGroupName', "默认分组"),
                    "includeRule": rule_camel.get('includeRule'),
                    "logicRuleList": rule_camel.get('logicRuleList'),
                    "exampleList": rule_camel.get('exampleList'),
                    "conditionalIdentifier": rule_camel.get('conditionalIdentifier', "anyone"),
                    "conditionList": rule_camel.get('conditionList', []),
                    "reviseOpinion": rule_camel.get('reviseOpinion', ""),
                    "creatorId": rule_camel.get('creatorId', 0),
                    "creatorName": rule_camel.get('creatorName', "admin"),
                    "version": rule_camel.get('version', 0),
                    "updateTime": rule_camel.get('updateTime', "2025-01-01T00:00:00"),
                    "result": True  # 默认通过，因为这是前端传入的原始规则
                }
                review_rule_dto_list.append(rule_dto)
                # 调试日志
                print(f"[DEBUG] 添加规则到 rule/confirm 请求: {rule_id}")
                log_debug(f"[DEBUG] 添加规则到 rule/confirm 请求: {rule_id}")
        
        # 构建标准格式的请求体
        rule_engine_payload = {
            "contractId": contract_id,
            "reviewRuleDtoList": review_rule_dto_list
        }
        
        # 详细打印标准格式请求
        print("=" * 80)
        print("🚀 RULE/CONFIRM API 标准格式请求详情")
        print("=" * 80)
        print(f"📡 URL: {rule_engine_url}")
        print(f"📋 请求方法: POST")
        print(f"⏱️  超时时间: 30秒")
        print("-" * 80)
        print("📦 标准格式请求体 (JSON):")
        print(json.dumps(rule_engine_payload, indent=2, ensure_ascii=False))
        print("-" * 80)
        print(f"📊 请求体大小: {len(json.dumps(rule_engine_payload, ensure_ascii=False))} 字符")
        print(f"🔢 reviewRuleDtoList 数量: {len(review_rule_dto_list)}")
        print(f"🆔 contractId: {contract_id}")
        print("=" * 80)
        
        print(f"[LOG] rule/confirm 请求: url={rule_engine_url}, payload={rule_engine_payload}")
        log_debug(f"[LOG] rule/confirm 请求: url={rule_engine_url}, payload={rule_engine_payload}")
        try:
            async with httpx.AsyncClient() as client:
                rule_engine_resp = await asyncio.wait_for(client.post(rule_engine_url, json=rule_engine_payload, timeout=30), timeout=60)
                rule_engine_resp_text = await rule_engine_resp.aread()
                print(f"[LOG] rule/confirm 响应: status={rule_engine_resp.status_code}, text={rule_engine_resp_text}")
                log_debug(f"[LOG] rule/confirm 响应: status={rule_engine_resp.status_code}, text={rule_engine_resp_text}")
                
                # 检查HTTP状态码
                if rule_engine_resp.status_code != 200:
                    # 记录错误日志
                    error_msg = f"rule/confirm 接口返回错误状态码: {rule_engine_resp.status_code}"
                    print(f"[ERROR] {error_msg}")
                    print(f"[ERROR] 响应内容: {rule_engine_resp_text[:500] if rule_engine_resp_text else None}")
                    log_debug(f"[ERROR] {error_msg}")
                    log_debug(f"[ERROR] 响应内容: {rule_engine_resp_text}")
                    
                    # 设置错误结果，让后续处理能够继续
                    rule_engine_result = {
                        "error": error_msg,
                        "error_type": "HTTP状态码错误",
                        "error_code": "HTTP_STATUS_ERROR",
                        "response_status": rule_engine_resp.status_code,
                        "response_text": rule_engine_resp_text[:500] if rule_engine_resp_text else None,
                        "fallback": True
                    }
                
                # 安全解析 JSON 响应
                try:
                    rule_engine_result = rule_engine_resp.json()
                    print(f"🔥🔥🔥 DEBUG: rule_engine_result 被赋值: {rule_engine_result} 🔥🔥🔥")
                    # 检查返回类型，如果不是字典则转换为字典
                    if not isinstance(rule_engine_result, dict):
                        print(f"[WARN] rule/confirm 响应不是字典类型: {type(rule_engine_result)}, 值: {rule_engine_result}")
                        log_debug(f"[WARN] rule/confirm 响应不是字典类型: {type(rule_engine_result)}, 值: {rule_engine_result}")
                        # 如果是布尔值，转换为字典格式
                        if isinstance(rule_engine_result, bool):
                            rule_engine_result = {"success": rule_engine_result, "message": "Boolean response converted to dict"}
                        else:
                            rule_engine_result = {"data": rule_engine_result, "message": "Non-dict response converted to dict"}
                except Exception as json_error:
                    # 记录错误日志
                    json_error_msg = f"解析 rule/confirm JSON 响应失败: {str(json_error)}"
                    print(f"[ERROR] {json_error_msg}")
                    print(f"[ERROR] 响应状态码: {rule_engine_resp.status_code}")
                    print(f"[ERROR] 响应内容: {rule_engine_resp_text[:500]}...")  # 只显示前500字符
                    log_debug(f"[ERROR] {json_error_msg}")
                    log_debug(f"[ERROR] 响应状态码: {rule_engine_resp.status_code}")
                    log_debug(f"[ERROR] 响应内容: {rule_engine_resp_text}")
                    
                    # 设置错误结果，让后续处理能够继续
                    rule_engine_result = {
                        "error": json_error_msg,
                        "error_type": "JSON解析失败",
                        "error_code": "JSON_PARSE_FAILED",
                        "response_status": rule_engine_resp.status_code,
                        "response_length": len(rule_engine_resp_text) if rule_engine_resp_text else 0,
                        "fallback": True  # 标记为兜底处理
                    }
                
                # 详细打印标准格式响应
                print("=" * 80)
                print("📥 RULE/CONFIRM API 标准格式响应详情")
                print("=" * 80)
                if rule_engine_result:
                    if "error" in rule_engine_result:
                        print(f"❌ 响应状态: 错误")
                        print(f"🚨 错误信息: {rule_engine_result['error']}")
                    else:
                        print(f"✅ 响应状态: 成功")
                        print(f"📊 响应体大小: {len(json.dumps(rule_engine_result, ensure_ascii=False))} 字符")
                        print(f"🔢 响应体键数量: {len(rule_engine_result.keys())}")
                        print(f"📋 响应体键列表: {list(rule_engine_result.keys())}")
                        
                        # 新增：详细分析 Java BaseResponse 格式
                        error_code = rule_engine_result.get('code') or rule_engine_result.get('errorCode')
                        if error_code is not None:
                            print(f"🔍 Java BaseResponse 格式分析:")
                            print(f"  - 错误码 (code): {error_code}")
                            print(f"  - 消息 (message): {rule_engine_result.get('message', 'N/A')}")
                            print(f"  - 数据 (data): {rule_engine_result.get('data', 'N/A')}")
                            
                            if error_code == 14000000:
                                print(f"  - 状态: 失败 (规则引擎执行失败)")
                            elif error_code == 20000000:
                                print(f"  - 状态: 成功")
                                data = rule_engine_result.get('data')
                                if isinstance(data, dict):
                                    print(f"  - JudgeResultDto 分析:")
                                    print(f"    * contractId: {data.get('contractId', 'N/A')}")
                                    print(f"    * ruleId: {data.get('ruleId', 'N/A')}")
                                    print(f"    * result: {data.get('result', 'N/A')}")
                            else:
                                print(f"  - 状态: 未知错误码")
                        
                        print("-" * 80)
                        print("📦 响应体 (JSON):")
                        print(json.dumps(rule_engine_result, indent=2, ensure_ascii=False))
                else:
                    print("❌ 响应状态: 无响应")
                print("=" * 80)
        except Exception as e:
            # 记录错误日志
            error_msg = f"rule/confirm调用失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            print(f"[ERROR] URL: {rule_engine_url}")
            print(f"[ERROR] Payload: {rule_engine_payload}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            log_debug(f"[ERROR] {error_msg}")
            log_debug(f"[ERROR] URL: {rule_engine_url}")
            log_debug(f"[ERROR] Payload: {rule_engine_payload}")
            log_debug(f"[ERROR] Exception type: {type(e).__name__}")
            
            # 设置错误结果，让后续处理能够继续
            rule_engine_result = {
                "error": f"rule/confirm 接口调用失败: {str(e)}",
                "error_type": "RULE_CONFIRM_CALL_FAILED",
                "error_code": "RULE_CONFIRM_FAILED",
                "fallback": True
            }
    elif need_rule_confirm:
        print(f"[WARN] 需要调用 rule/confirm 但缺少必要参数: contract_id={contract_id}, rules_count={len(censored_rules)}")
        log_debug(f"[WARN] 需要调用 rule/confirm 但缺少必要参数: contract_id={contract_id}, rules_count={len(censored_rules)}")
    else:
        print(f"[INFO] 无需调用 rule/confirm: need_rule_confirm={need_rule_confirm}, censored_rules_count={len(censored_rules)}")
        log_debug(f"[INFO] 无需调用 rule/confirm: need_rule_confirm={need_rule_confirm}, censored_rules_count={len(censored_rules)}")
    
    # 检查 rule/confirm 结果
    print(f"===============================================================================")
    print(f"[STREAM_PRE_CHECK] 🔍 在流式响应开始前检查 rule/confirm 结果...")
    print(f"[STREAM_PRE_CHECK] ⏰ 时间戳: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[STREAM_PRE_CHECK] 🔍 强制检查 rule_engine_result:")
    print(f"[STREAM_PRE_CHECK]   - 类型: {type(rule_engine_result)}")
    print(f"[STREAM_PRE_CHECK]   - 值: {rule_engine_result}")
    print(f"[STREAM_PRE_CHECK]   - 是否为字典: {isinstance(rule_engine_result, dict)}")
    if isinstance(rule_engine_result, dict):
        print(f"[STREAM_PRE_CHECK]   - 错误码: {rule_engine_result.get('code') or rule_engine_result.get('errorCode')}")
        print(f"[STREAM_PRE_CHECK]   - 错误信息: {rule_engine_result.get('error')}")
        print(f"[STREAM_PRE_CHECK]   - 兜底标记: {rule_engine_result.get('fallback')}")
    log_debug(f"[STREAM_PRE_CHECK] 检查 rule/confirm 结果，rule_engine_result: {rule_engine_result}")
    
    if rule_engine_result and isinstance(rule_engine_result, dict):
        # 检查是否有错误信息
        if rule_engine_result.get('error') or rule_engine_result.get('fallback'):
            error_info = rule_engine_result.get('error', 'Unknown error')
            print(f"[STREAM_PRE_CHECK] ❌ 发现错误信息: {error_info}")
            print(f"[STREAM_PRE_CHECK] 🚨 准备抛出 RuleConfirmException (error/fallback)")
            
            raise RuleConfirmException(
                f"rule/confirm 接口调用失败: {error_info}",
                details={
                    "error_type": rule_engine_result.get('error_type', 'UNKNOWN'),
                    "error_code": rule_engine_result.get('error_code', 'UNKNOWN'),
                    "response_data": rule_engine_result
                }
            )
        
        # 检查错误码
        error_code = rule_engine_result.get('code') or rule_engine_result.get('errorCode')
        print(f"[STREAM_PRE_CHECK] 🔢 检查错误码: {error_code}")
        
        if error_code == 14000000:
            error_message = rule_engine_result.get('message', '规则引擎执行失败')
            error_description = rule_engine_result.get('description', '')
            print(f"[STREAM_PRE_CHECK] ❌ 发现错误码 14000000!")
            print(f"[STREAM_PRE_CHECK] 📝 错误消息: {error_message}")
            print(f"[STREAM_PRE_CHECK] 📄 错误描述: {error_description}")
            print(f"[STREAM_PRE_CHECK] 🚨 准备抛出 RuleConfirmException (错误码 14000000)")
            
            raise RuleConfirmException(
                f"rule/confirm 接口执行失败: {error_message}",
                details={
                    "error_code": error_code,
                    "error_message": error_message,
                    "error_description": error_description,
                    "response_data": rule_engine_result
                }
            )
        elif error_code and error_code not in [20000000, 10000000]:
            error_message = rule_engine_result.get('message', '未知错误')
            print(f"[STREAM_PRE_CHECK] ❌ 发现未知错误码: {error_code}")
            print(f"[STREAM_PRE_CHECK] 📝 错误消息: {error_message}")
            print(f"[STREAM_PRE_CHECK] 🚨 准备抛出 RuleConfirmException (未知错误码)")
            
            raise RuleConfirmException(
                f"rule/confirm 接口返回未知错误码: {error_code}",
                details={
                    "error_code": error_code,
                    "error_message": error_message,
                    "response_data": rule_engine_result
                }
            )
        else:
            print(f"[STREAM_PRE_CHECK] ✅ rule/confirm 结果检查通过，错误码: {error_code}")
    else:
        print(f"[STREAM_PRE_CHECK] ⚠️  rule_engine_result 为空或非字典类型: {type(rule_engine_result)}")
    
    print(f"[STREAM_PRE_CHECK] ✅ 检查完成，开始流式响应...")
    print(f"===============================================================================")

    return StreamingResponse(event_stream(), media_type="text/event-stream")

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
        # 已删除 volcenginesdkarkruntime 导入
        
        # 简化的响应处理（已删除 Ark 客户端）
        response_text = "这是一个简化的结构化审查响应。实际应用中需要集成大模型服务。"
        
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

@app.get("/debug/rule-confirm-results/{session_id}")
async def debug_rule_confirm_results(session_id: str, db: Session = Depends(get_session)):
    """
    调试接口：查看指定会话的 rule/confirm 结果存储情况
    """
    try:
        from ContractAudit.models import get_confirm_review_rule_results
        
        results = get_confirm_review_rule_results(db, session_id)
        
        debug_data = []
        for result in results:
            debug_data.append({
                "id": result.id,
                "session_id": result.session_id,
                "rule_id": result.rule_id,
                "rule_name": result.rule_name,
                "review_result": result.review_result,
                "risk_level": result.risk_level,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "matched_content": result.matched_content,
                "analysis": result.analysis
            })
        
        return {
            "session_id": session_id,
            "total_results": len(debug_data),
            "results": debug_data,
            "pass_count": len([r for r in debug_data if r['review_result'] == 'pass']),
            "done_count": len([r for r in debug_data if r['review_result'] == 'done'])
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "session_id": session_id
        }

def validate_and_convert_condition_info(condition_list):
    """递归处理 conditionList，确保 conditionInfo 字段格式正确"""
    if not condition_list:
        return condition_list
    new_list = []
    for cond in condition_list:
        if isinstance(cond, dict) and 'conditionInfo' in cond:
            val = cond['conditionInfo']
            # 确保 conditionInfo 是字符串格式，Java 后端期望字符串
            if not isinstance(val, str):
                # 如果不是字符串，转换为 JSON 字符串
                cond['conditionInfo'] = json.dumps(val, ensure_ascii=False)
            else:
                # 如果是字符串，验证是否为有效的 JSON 格式
                try:
                    # 验证 JSON 格式是否正确，但不改变类型
                    json.loads(val)
                except Exception:
                    # 如果不是有效的 JSON，保持原样
                    pass
        new_list.append(cond)
    return new_list

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
    port = int(os.getenv("PORT", "8010"))
    print(f"启动服务器在 {host}:{port}")
    print("按 Ctrl+C 可优雅关闭服务")
    uvicorn.run(
        "ContractAudit.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="debug"
    )
