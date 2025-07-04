"""
ContractAudit模块主入口文件
基于LangChain的合同审计对话系统
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import uuid
import sys
# 处理相对导入问题 - 支持直接运行和模块导入
# 添加项目根目录到Python路径
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入外部路由
try:
    if __name__ == "__main__":
        # 直接运行时，跳过external_routes导入，因为它有相对导入问题
        external_router = None
        print("跳过external_routes导入（直接运行模式）")
    else:
        from .external_routes import router as external_router
except ImportError as e:
    print(f"无法导入external_routes: {e}")
    external_router = None

try:
    # 只导入完整版聊天管理器
    if __name__ == "__main__":
        from ContractAudit.chat import get_chat_manager, ChatSession
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
            import time
            
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

# 创建FastAPI应用
app = FastAPI(
    title="ContractAudit Chat System",
    description="基于LangChain的合同审计对话系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    print("ContractAudit Chat System starting up...")
    print(f"Active sessions: {len(chat_manager.sessions)}")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("ContractAudit Chat System shutting down...")
    print(f"Cleaning up {len(chat_manager.sessions)} sessions")

# 包含外部路由（如果可用）
if external_router is not None:
    app.include_router(external_router)
    print("✅ 外部路由已加载")
else:
    print("⚠️  外部路由未加载（直接运行模式或导入失败）")

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
