#!/usr/bin/env python3
"""
简化的FastAPI服务器，用于测试
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

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
class ChatRequest(BaseModel):
    session_id: str
    message: str

# 路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "ContractAudit Chat System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "Service is running"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """发送聊天消息"""
    return {
        "session_id": request.session_id,
        "response": f"收到消息: {request.message}",
        "timestamp": "2024-01-01T00:00:00",
        "error": False
    }

@app.get("/docs")
async def docs():
    """API文档"""
    return {"message": "API文档可通过 /docs 访问"}

if __name__ == "__main__":
    print("启动简化的合同审计系统...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 