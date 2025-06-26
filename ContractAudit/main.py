"""
ContractAudit模块主入口文件
基于LangChain的合同审计对话系统
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import uuid
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 优先尝试导入简化版本
    from ContractAudit.chat_simple import chat_manager, ChatSession
    print("使用简化版聊天管理器")
except ImportError:
    try:
        from chat_simple import chat_manager, ChatSession
        print("使用简化版聊天管理器")
    except ImportError:
        try:
            # 如果简化版本不可用，尝试完整版本
            from ContractAudit.chat import chat_manager, ChatSession
            print("使用完整版聊天管理器")
        except ImportError as e:
            print(f"导入错误: {e}")
            print("请确保在正确的目录下运行，或者安装所有依赖包")
            sys.exit(1)

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

if __name__ == "__main__":
    import uvicorn
    # 从环境变量获取主机和端口，默认为实际网络接口
    host = os.getenv("HOST", "172.20.237.94")  # 使用实际网络接口IP
    port = int(os.getenv("PORT", "8001"))
    
    print(f"启动服务器在 {host}:{port}")
    print("如果外部访问仍有问题，请尝试使用 0.0.0.0 作为 HOST")
    
    uvicorn.run(app, host=host, port=port)
