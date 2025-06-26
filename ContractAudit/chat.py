"""
基于LangChain的合同审计对话功能模块
企业级聊天管理系统，支持多用户会话、文档处理和智能对话
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Milvus
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader
from langchain_core.documents import Document

# 尝试导入火山引擎Ark，如果不可用则使用模拟实现
try:
    from volcenginesdkarkruntime import Ark
    ARK_AVAILABLE = True
except ImportError:
    ARK_AVAILABLE = False
    print("警告: volcenginesdkarkruntime 模块不可用，将使用模拟LLM实现")
    
    # 创建模拟的Ark类
    class Ark:
        def __init__(self, api_key=None, base_url=None, timeout=None, max_retries=None):
            self.api_key = api_key
            self.base_url = base_url
            self.timeout = timeout
            self.max_retries = max_retries
            print("使用模拟LLM客户端")

from ContractAudit.config import settings
from ContractAudit.logger import get_logger, log_performance_metric, log_error
from .prompt_template import PromptFactory


@dataclass
class ChatMessage:
    """
    聊天消息数据类
    存储单条聊天消息的完整信息
    """
    id: str  # 消息唯一标识符
    role: str  # 消息角色："user" 或 "assistant"
    content: str  # 消息内容
    timestamp: datetime  # 消息时间戳
    metadata: Optional[Dict[str, Any]] = None  # 消息元数据（如错误信息、处理时间等）

    def to_dict(self) -> Dict[str, Any]:
        """
        将消息对象转换为字典格式
        
        Returns:
            Dict[str, Any]: 消息的字典表示
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class ChatSession:
    """
    聊天会话数据类
    管理单个用户的聊天会话，包含会话信息和消息历史
    """
    session_id: str  # 会话唯一标识符
    user_id: str  # 用户标识符
    contract_file: Optional[str] = None  # 关联的合同文件路径
    created_at: datetime = None  # 会话创建时间
    updated_at: datetime = None  # 会话最后更新时间
    messages: List[ChatMessage] = None  # 消息历史列表

    def __post_init__(self):
        """初始化后处理，设置默认值"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.messages is None:
            self.messages = []

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        添加消息到会话
        
        Args:
            role: 消息角色（"user" 或 "assistant"）
            content: 消息内容
            metadata: 消息元数据
        """
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
        """
        获取消息数量
        
        Returns:
            int: 消息总数
        """
        return len(self.messages)

    def get_recent_messages(self, count: int = 10) -> List[ChatMessage]:
        """
        获取最近的消息
        
        Args:
            count: 返回的消息数量
            
        Returns:
            List[ChatMessage]: 最近的消息列表
        """
        return self.messages[-count:] if len(self.messages) > count else self.messages

    def to_dict(self) -> Dict[str, Any]:
        """
        将会话对象转换为字典格式
        
        Returns:
            Dict[str, Any]: 会话的字典表示
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "contract_file": self.contract_file,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "message_count": self.get_message_count()
        }


class ContractChatManager:
    """
    合同聊天管理器
    核心业务逻辑类，负责会话管理、文档处理和智能对话
    """
    
    def __init__(self):
        """初始化聊天管理器"""
        self.sessions: Dict[str, ChatSession] = {}  # 会话存储字典
        self.vector_store: Optional[Milvus] = None  # 向量存储实例
        self.llm_client: Optional[Ark] = None  # LLM客户端
        self.embeddings: Optional[HuggingFaceEmbeddings] = None  # 嵌入模型
        self.text_splitter: Optional[RecursiveCharacterTextSplitter] = None  # 文本分割器
        self.prompt_factory: PromptFactory = PromptFactory()  # 提示词工厂
        
        # 初始化日志记录器
        self.logger = get_logger("ContractChatManager")
        
        # 初始化组件
        self._initialize_components()
        
        self.logger.info("合同聊天管理器初始化完成")
    
    def _initialize_components(self):
        """
        初始化各种组件
        包括嵌入模型、文本分割器、LLM客户端等
        """
        try:
            # 初始化嵌入模型
            self.logger.info("正在初始化嵌入模型...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL_NAME,
                model_kwargs={'device': settings.EMBEDDING_DEVICE}
            )
            self.logger.info(f"嵌入模型初始化成功: {settings.EMBEDDING_MODEL_NAME}")
        except Exception as e:
            self.logger.error(f"嵌入模型初始化失败: {e}")
            self.embeddings = None
        
        # 初始化文本分割器
        try:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?"]
            )
            self.logger.info("文本分割器初始化成功")
        except Exception as e:
            self.logger.error(f"文本分割器初始化失败: {e}")
            self.text_splitter = None
        
        # 初始化LLM客户端
        try:
            if settings.ARK_API_KEY and ARK_AVAILABLE:
                self.llm_client = Ark(
                    api_key=settings.ARK_API_KEY,
                    base_url=settings.ARK_BASE_URL,
                    timeout=settings.ARK_TIMEOUT,
                    max_retries=settings.ARK_MAX_RETRIES
                )
                self.logger.info("LLM客户端初始化成功")
            else:
                if not ARK_AVAILABLE:
                    self.logger.warning("volcenginesdkarkruntime模块不可用，使用模拟LLM客户端")
                else:
                    self.logger.warning("ARK_API_KEY未配置，使用模拟LLM客户端")
                self.llm_client = Ark()  # 使用模拟客户端
        except Exception as e:
            self.logger.error(f"LLM客户端初始化失败: {e}")
            self.llm_client = None
    
    @log_performance_metric
    def create_session(self, user_id: str, contract_file: Optional[str] = None) -> str:
        """
        创建新的聊天会话
        
        Args:
            user_id: 用户标识符
            contract_file: 可选的合同文件路径
            
        Returns:
            str: 新创建的会话ID
            
        Raises:
            ValueError: 当用户ID为空时
        """
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        # 检查用户会话数量限制
        user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        if len(user_sessions) >= settings.MAX_SESSIONS_PER_USER:
            self.logger.warning(f"用户 {user_id} 的会话数量已达到限制")
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
        
        self.logger.info(f"创建新会话: {session_id}, 用户: {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        获取聊天会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[ChatSession]: 会话对象，如果不存在则返回None
        """
        session = self.sessions.get(session_id)
        if session:
            # 检查会话是否超时
            if self._is_session_expired(session):
                self.logger.info(f"会话 {session_id} 已超时，自动删除")
                self.delete_session(session_id)
                return None
        return session
    
    def _is_session_expired(self, session: ChatSession) -> bool:
        """
        检查会话是否超时
        
        Args:
            session: 会话对象
            
        Returns:
            bool: 是否超时
        """
        timeout_hours = settings.SESSION_TIMEOUT_HOURS
        if timeout_hours <= 0:
            return False
        
        from datetime import timedelta
        timeout_threshold = datetime.now() - timedelta(hours=timeout_hours)
        return session.updated_at < timeout_threshold
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除聊天会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        if session_id in self.sessions:
            session = self.sessions[session_id]
            del self.sessions[session_id]
            self.logger.info(f"删除会话: {session_id}, 用户: {session.user_id}")
            return True
        return False
    
    @log_performance_metric
    def load_contract_to_vectorstore(self, contract_file: str) -> bool:
        """
        将合同文档加载到向量存储
        
        Args:
            contract_file: 合同文件路径
            
        Returns:
            bool: 加载是否成功
        """
        start_time = time.time()
        
        try:
            # 验证文件存在
            if not os.path.exists(contract_file):
                raise FileNotFoundError(f"合同文件不存在: {contract_file}")
            
            # 验证文件大小
            file_size = os.path.getsize(contract_file)
            if file_size > settings.MAX_DOCUMENT_SIZE:
                raise ValueError(f"文件大小超过限制: {file_size} bytes")
            
            # 验证文件类型
            file_ext = Path(contract_file).suffix.lower()
            if file_ext not in settings.ALLOWED_FILE_TYPES:
                raise ValueError(f"不支持的文件类型: {file_ext}")
            
            self.logger.info(f"开始加载合同文件: {contract_file}")
            
            # 加载文档
            loader = Docx2txtLoader(contract_file)
            documents = loader.load()
            
            if not documents:
                raise ValueError("文档加载失败，未获取到内容")
            
            # 分割文档
            if not self.text_splitter:
                raise RuntimeError("文本分割器未初始化")
            
            texts = self.text_splitter.split_documents(documents)
            self.logger.info(f"文档分割完成，共 {len(texts)} 个文本块")
            
            # 创建向量存储
            if not self.embeddings:
                raise RuntimeError("嵌入模型未初始化")
            
            self.vector_store = Milvus.from_documents(
                documents=texts,
                embedding=self.embeddings,
                collection_name=settings.MILVUS_COLLECTION_NAME,
                connection_args=settings.milvus_connection_args
            )
            
            processing_time = time.time() - start_time
            self.logger.info(f"合同加载成功: {contract_file}, 处理时间: {processing_time:.2f}s")
            
            return True
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"合同加载失败: {contract_file}, 错误: {e}, 处理时间: {processing_time:.2f}s")
            log_error(e, {"contract_file": contract_file, "processing_time": processing_time})
            return False
    
    def _get_prompt_template(self, question: str) -> ChatPromptTemplate:
        """
        根据问题类型选择合适的提示模板
        
        Args:
            question: 用户问题
            
        Returns:
            ChatPromptTemplate: 合适的提示模板
        """
        # 简单的关键词匹配来选择模板
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
    
    def _retrieve_relevant_context(self, question: str, top_k: int = 5) -> str:
        """
        检索相关的合同内容
        
        Args:
            question: 用户问题
            top_k: 返回的相关文档数量
            
        Returns:
            str: 相关的合同内容
        """
        if not self.vector_store:
            return "无法检索合同内容，向量存储未初始化。"
        
        try:
            docs = self.vector_store.similarity_search(question, k=top_k)
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            self.logger.error(f"检索上下文失败: {e}")
            log_error(e, {"question": question, "top_k": top_k})
            return "检索合同内容时出现错误。"
    
    def _format_chat_history(self, messages: List[ChatMessage]) -> List:
        """
        格式化聊天历史为LangChain消息格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List: 格式化后的消息列表
        """
        formatted_history = []
        # 只保留最近的消息以避免上下文过长
        recent_messages = messages[-10:]
        
        for msg in recent_messages:
            if msg.role == "user":
                formatted_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                formatted_history.append(AIMessage(content=msg.content))
        
        return formatted_history
    
    @log_performance_metric
    def chat(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        处理用户消息并返回回复
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            
        Returns:
            Dict[str, Any]: 包含回复和元数据的字典
        """
        start_time = time.time()
        
        # 获取会话
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        try:
            # 验证消息长度
            if len(user_message) > 10000:  # 10KB限制
                raise ValueError("消息长度超过限制")
            
            # 添加用户消息到会话
            session.add_message("user", user_message)
            
            # 检查消息数量限制
            if len(session.messages) > settings.MAX_MESSAGES_PER_SESSION:
                # 保留最近的消息
                session.messages = session.messages[-settings.MAX_MESSAGES_PER_SESSION:]
                self.logger.warning(f"会话 {session_id} 消息数量达到限制，已清理旧消息")
            
            # 检索相关上下文
            context = self._retrieve_relevant_context(user_message)
            
            # 格式化聊天历史
            chat_history = self._format_chat_history(session.messages)
            
            # 获取合适的提示模板
            prompt = self._get_prompt_template(user_message)
            
            # 构建对话链
            chain = (
                {
                    "context": lambda x: x["context"],
                    "chat_history": lambda x: x["chat_history"],
                    "question": lambda x: x["question"],
                    "contract_content": lambda x: x["context"]  # 为其他模板提供合同内容
                }
                | prompt
                | self._get_llm_chain()
                | StrOutputParser()
            )
            
            # 执行对话
            response = chain.invoke({
                "context": context,
                "chat_history": chat_history,
                "question": user_message,
                "contract_content": context
            })
            
            # 添加助手回复到会话
            session.add_message("assistant", response)
            
            response_time = time.time() - start_time
            
            result = {
                "session_id": session_id,
                "response": response,
                "context_used": context[:200] + "..." if len(context) > 200 else context,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time
            }
            
            self.logger.info(f"聊天处理完成: {session_id}, 响应时间: {response_time:.2f}s")
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"处理消息时出现错误: {str(e)}"
            
            # 添加错误消息到会话
            session.add_message("assistant", error_msg, {"error": True, "error_type": type(e).__name__})
            
            self.logger.error(f"聊天处理失败: {session_id}, 错误: {e}, 响应时间: {response_time:.2f}s")
            log_error(e, {"session_id": session_id, "user_message": user_message, "response_time": response_time})
            
            return {
                "session_id": session_id,
                "response": error_msg,
                "error": True,
                "timestamp": datetime.now().isoformat(),
                "response_time": response_time
            }
    
    def _get_llm_chain(self):
        """
        获取LLM调用链
        
        Returns:
            可调用的LLM链
        """
        if not self.llm_client:
            # 如果没有LLM客户端，返回一个简单的回复
            return lambda x: "抱歉，LLM服务暂时不可用。"
        
        # 这里需要根据实际的Ark API来调整
        # 暂时返回一个简单的实现
        return lambda x: self._call_ark_llm(x)
    
    def _call_ark_llm(self, prompt: str) -> str:
        """
        调用Ark LLM
        
        Args:
            prompt: 提示词
            
        Returns:
            str: LLM回复
        """
        try:
            if not ARK_AVAILABLE:
                # 使用模拟回复
                return f"基于合同内容，我为您分析如下：{prompt[:100]}...\n\n注意：当前使用模拟LLM，实际部署时请配置真实的LLM服务。"
            
            # 这里需要根据实际的Ark API来调整
            # 暂时返回一个示例回复
            return f"基于合同内容，我为您分析如下：{prompt[:100]}..."
        except Exception as e:
            self.logger.error(f"调用LLM失败: {e}")
            return f"调用LLM时出现错误: {str(e)}"
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话历史数据
        """
        session = self.get_session(session_id)
        if session:
            return session.to_dict()
        return None
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有会话
        
        Args:
            user_id: 可选的用户ID过滤器
            
        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        sessions = []
        for session in self.sessions.values():
            if user_id is None or session.user_id == user_id:
                sessions.append(session.to_dict())
        
        # 按更新时间排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的会话
        
        Returns:
            int: 清理的会话数量
        """
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            self.logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
        
        return len(expired_sessions)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            Dict[str, Any]: 系统统计信息
        """
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
            "vector_store_available": self.vector_store is not None,
            "llm_client_available": self.llm_client is not None,
            "embeddings_available": self.embeddings is not None,
            "ark_available": ARK_AVAILABLE,
            "user_stats": user_stats
        }


# 全局聊天管理器实例
chat_manager = ContractChatManager()
