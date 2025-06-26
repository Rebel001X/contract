"""
简化版合同审计聊天功能模块
避免复杂依赖，便于开发和测试
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# 基础配置
class Settings:
    """基础配置类"""
    MAX_SESSIONS_PER_USER = 10
    MAX_MESSAGES_PER_SESSION = 100
    SESSION_TIMEOUT_HOURS = 24
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES = ['.docx', '.doc', '.pdf', '.txt']
    
    # 模拟配置
    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE = "cpu"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MILVUS_COLLECTION_NAME = "contract_audit"
    
    # Milvus连接配置
    @property
    def milvus_connection_args(self):
        return {
            "host": "localhost",
            "port": "19530"
        }

settings = Settings()

@dataclass
class ChatMessage:
    """聊天消息数据类"""
    id: str
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }

@dataclass
class ChatSession:
    """聊天会话数据类"""
    session_id: str
    user_id: str
    contract_file: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    messages: List[ChatMessage] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.messages is None:
            self.messages = []

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        message = ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_message_count(self) -> int:
        return len(self.messages)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "contract_file": self.contract_file,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "message_count": self.get_message_count()
        }

class SimplePromptFactory:
    """简化的提示词工厂"""
    
    def get_template(self, template_type: str) -> str:
        """获取提示词模板"""
        templates = {
            "basic": """你是一个专业的合同审计助手。请基于以下合同内容回答用户问题：

合同内容：
{contract_content}

聊天历史：
{chat_history}

用户问题：{question}

请提供专业、准确的回答：""",

            "risk_analysis": """作为合同风险分析专家，请分析以下合同中的风险点：

合同内容：
{contract_content}

用户问题：{question}

请从以下方面进行分析：
1. 法律风险
2. 商业风险
3. 财务风险
4. 操作风险
5. 建议措施""",

            "clause_analysis": """请分析以下合同条款：

合同内容：
{contract_content}

用户问题：{question}

请从以下方面进行分析：
1. 条款含义
2. 权利义务
3. 潜在问题
4. 改进建议""",

            "legal_advice": """作为法律顾问，请为以下合同问题提供专业建议：

合同内容：
{contract_content}

用户问题：{question}

请提供：
1. 法律依据
2. 风险评估
3. 建议措施
4. 注意事项""",

            "summary": """请对以下合同进行总结：

合同内容：
{contract_content}

用户问题：{question}

请提供：
1. 合同类型
2. 主要条款
3. 关键要点
4. 重要日期
5. 风险提示""",

            "negotiation": """作为谈判顾问，请为以下合同提供谈判建议：

合同内容：
{contract_content}

用户问题：{question}

请提供：
1. 谈判要点
2. 可协商条款
3. 底线建议
4. 策略建议"""
        }
        
        return templates.get(template_type, templates["basic"])

class SimpleContractChatManager:
    """简化的合同聊天管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.contract_content: str = ""
        self.prompt_factory = SimplePromptFactory()
        print("简化版合同聊天管理器初始化完成")
    
    def create_session(self, user_id: str, contract_file: Optional[str] = None) -> str:
        """创建新的聊天会话"""
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        # 检查用户会话数量限制
        user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        if len(user_sessions) >= settings.MAX_SESSIONS_PER_USER:
            print(f"用户 {user_id} 的会话数量已达到限制")
            # 删除最旧的会话
            oldest_session = min(user_sessions, key=lambda s: s.created_at)
            self.delete_session(oldest_session.session_id)
        
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            contract_file=contract_file
        )
        self.sessions[session_id] = session
        
        print(f"创建新会话: {session_id}, 用户: {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取聊天会话"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """删除聊天会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            del self.sessions[session_id]
            print(f"删除会话: {session_id}, 用户: {session.user_id}")
            return True
        return False
    
    def load_contract_to_vectorstore(self, contract_file: str) -> bool:
        """模拟加载合同文档"""
        try:
            if not os.path.exists(contract_file):
                raise FileNotFoundError(f"合同文件不存在: {contract_file}")
            
            # 简单读取文件内容（仅支持文本文件）
            if contract_file.endswith('.txt'):
                with open(contract_file, 'r', encoding='utf-8') as f:
                    self.contract_content = f.read()
            else:
                # 对于其他文件类型，使用模拟内容
                self.contract_content = f"模拟合同内容 - 文件: {contract_file}\n\n这是一个示例合同，包含各种条款和条件。"
            
            print(f"合同加载成功: {contract_file}")
            return True
                
        except Exception as e:
            print(f"合同加载失败: {contract_file}, 错误: {e}")
            return False
    
    def _get_prompt_template(self, question: str) -> str:
        """根据问题类型选择合适的提示模板"""
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ["风险", "风险点", "风险分析"]):
            return self.prompt_factory.get_template("risk_analysis")
        elif any(keyword in question_lower for keyword in ["条款", "分析条款", "条款分析"]):
            return self.prompt_factory.get_template("clause_analysis")
        elif any(keyword in question_lower for keyword in ["法律", "法律建议", "法律问题"]):
            return self.prompt_factory.get_template("legal_advice")
        elif any(keyword in question_lower for keyword in ["摘要", "总结", "概述"]):
            return self.prompt_factory.get_template("summary")
        elif any(keyword in question_lower for keyword in ["谈判", "协商", "建议"]):
            return self.prompt_factory.get_template("negotiation")
        else:
            return self.prompt_factory.get_template("basic")
    
    def _format_chat_history(self, messages: List[ChatMessage]) -> str:
        """格式化聊天历史"""
        if not messages:
            return "无聊天历史"
        
        history = []
        for msg in messages[-5:]:  # 只保留最近5条消息
            role = "用户" if msg.role == "user" else "助手"
            history.append(f"{role}: {msg.content}")
        
        return "\n".join(history)
    
    def chat(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """处理用户消息并返回回复"""
        start_time = time.time()
        
        # 获取会话
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        try:
            # 验证消息长度
            if len(user_message) > 10000:
                raise ValueError("消息长度超过限制")
            
            # 添加用户消息到会话
            session.add_message("user", user_message)
            
            # 检查消息数量限制
            if len(session.messages) > settings.MAX_MESSAGES_PER_SESSION:
                session.messages = session.messages[-settings.MAX_MESSAGES_PER_SESSION:]
                print(f"会话 {session_id} 消息数量达到限制，已清理旧消息")
            
            # 获取提示模板
            prompt_template = self._get_prompt_template(user_message)
            
            # 格式化聊天历史
            chat_history = self._format_chat_history(session.messages)
            
            # 生成回复
            response = self._generate_response(prompt_template, user_message, chat_history)
            
            # 添加助手回复到会话
            session.add_message("assistant", response)
            
            response_time = time.time() - start_time
            
            result = {
                "session_id": session_id,
                "response": response,
                "context_used": self.contract_content[:200] + "..." if len(self.contract_content) > 200 else self.contract_content,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time
            }
            
            print(f"聊天处理完成: {session_id}, 响应时间: {response_time:.2f}s")
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"处理消息时出现错误: {str(e)}"
            
            # 添加错误消息到会话
            session.add_message("assistant", error_msg, {"error": True, "error_type": type(e).__name__})
            
            print(f"聊天处理失败: {session_id}, 错误: {e}, 响应时间: {response_time:.2f}s")
            
            return {
                "session_id": session_id,
                "response": error_msg,
                "error": True,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time
            }
    
    def _generate_response(self, prompt_template: str, question: str, chat_history: str) -> str:
        """生成回复（模拟LLM）"""
        # 使用模板生成回复
        response = prompt_template.format(
            contract_content=self.contract_content or "暂无合同内容",
            chat_history=chat_history,
            question=question
        )
        
        # 模拟LLM处理
        if "风险" in question.lower():
            return f"基于合同内容，我为您分析风险点：\n\n{response}\n\n注意：这是模拟回复，实际部署时请配置真实的LLM服务。"
        elif "条款" in question.lower():
            return f"条款分析结果：\n\n{response}\n\n注意：这是模拟回复，实际部署时请配置真实的LLM服务。"
        elif "法律" in question.lower():
            return f"法律建议：\n\n{response}\n\n注意：这是模拟回复，实际部署时请配置真实的LLM服务。"
        else:
            return f"回复：\n\n{response}\n\n注意：这是模拟回复，实际部署时请配置真实的LLM服务。"
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话历史"""
        session = self.get_session(session_id)
        if session:
            return session.to_dict()
        return None
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []
        for session in self.sessions.values():
            if user_id is None or session.user_id == user_id:
                sessions.append(session.to_dict())
        
        # 按更新时间排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        total_sessions = len(self.sessions)
        total_messages = sum(len(session.messages) for session in self.sessions.values())
        
        # 按用户分组统计
        user_stats = {}
        for session in self.sessions.values():
            user_id = session.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {"sessions": 0, "messages": 0}
            user_stats[user_id]["sessions"] += 1
            user_stats[user_id]["messages"] += len(session.messages)
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "active_users": len(user_stats),
            "vector_store_available": False,  # 简化版本不使用向量存储
            "llm_client_available": False,    # 简化版本不使用真实LLM
            "embeddings_available": False,    # 简化版本不使用嵌入模型
            "ark_available": False,           # 简化版本不使用Ark
            "user_stats": user_stats
        }

# 全局聊天管理器实例
chat_manager = SimpleContractChatManager() 