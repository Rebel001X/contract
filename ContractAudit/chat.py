"""
基于LangChain的合同审计对话功能模块
企业级聊天管理系统，支持多用户会话、文档处理和智能对话
"""

import os
import sys

# 强制设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# 确保 Python3 默认编码为 UTF-8
if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding('utf-8')

print("系统默认编码:", sys.getdefaultencoding())
print("环境变量 PYTHONIOENCODING:", os.environ.get("PYTHONIOENCODING"))

# Monkey patch for requests/httpx to force UTF-8
try:
    import requests
    import json
    original_dumps = json.dumps
    def safe_dumps(obj, **kwargs):
        kwargs.setdefault('ensure_ascii', False)
        # 移除 encoding 参数，Python 3 不支持
        if 'encoding' in kwargs:
            del kwargs['encoding']
        return original_dumps(obj, **kwargs)
    json.dumps = safe_dumps
    print("✅ JSON dumps monkey patch applied")
except Exception as e:
    print(f"⚠️ JSON monkey patch failed: {e}")

# Monkey patch for httpx to force UTF-8 encoding in headers
try:
    import httpx
    original_normalize_header_value = httpx._models._normalize_header_value
    def safe_normalize_header_value(value, encoding=None):
        if encoding is None:
            encoding = "utf-8"
        return original_normalize_header_value(value, encoding)
    httpx._models._normalize_header_value = safe_normalize_header_value
    print("✅ httpx header encoding monkey patch applied")
except Exception as e:
    print(f"⚠️ httpx monkey patch failed: {e}")

# Monkey patch for httpx Headers class
try:
    original_headers_init = httpx.Headers.__init__
    def safe_headers_init(self, headers=None, encoding=None):
        if encoding is None:
            encoding = "utf-8"
        return original_headers_init(self, headers, encoding)
    httpx.Headers.__init__ = safe_headers_init
    print("✅ httpx Headers monkey patch applied")
except Exception as e:
    print(f"⚠️ httpx Headers monkey patch failed: {e}")

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
from volcenginesdkarkruntime import Ark
# 尝试导入配置和日志模块，如果不可用则使用默认配置
try:
    from ContractAudit.config import settings
    from logger import get_logger, log_performance_metric, log_error
    from prompt_template import PromptFactory
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("警告: 配置模块不可用，使用默认配置")
    
    # 创建默认配置
    class Settings:
        MAX_SESSIONS_PER_USER = 10
        MAX_MESSAGES_PER_SESSION = 100
        SESSION_TIMEOUT_HOURS = 24
        MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
        ALLOWED_FILE_TYPES = ['.docx', '.doc', '.pdf', '.txt']
        EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
        EMBEDDING_DEVICE = "cpu"
        CHUNK_SIZE = 1000
        CHUNK_OVERLAP = 200
        MILVUS_COLLECTION_NAME = "contract_audit"
        ARK_API_KEY = None
        ARK_BASE_URL = None
        ARK_TIMEOUT = 30
        ARK_MAX_RETRIES = 3
    
    settings = Settings()
    
    # 创建默认日志函数
    def get_logger(name):
        import logging
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def log_performance_metric(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    def log_error(error, context=None):
        print(f"错误: {error}")
    
    # 创建默认提示词工厂
    class PromptFactory:
        def get_template(self, template_type: str) -> ChatPromptTemplate:
            # 返回一个简单的模板
            return ChatPromptTemplate.from_template("请回答用户问题: {question}")

# 尝试导入火山引擎Ark，如果不可用则使用模拟实现
try:
    from volcenginesdkarkruntime import Ark
    ARK_AVAILABLE = True
    print("✅ Ark 模块导入成功")
except ImportError:
    ARK_AVAILABLE = False
    print("❌ Ark 模块导入失败")
    print("使用模拟 Ark 实现，LLM 功能将受限")

# 创建模拟的Ark类（如果导入失败）
if not ARK_AVAILABLE:
    class Ark:
        def __init__(self, api_key=None, base_url=None, timeout=None, max_retries=None):
            self.api_key = api_key
            self.base_url = base_url
            self.timeout = timeout
            self.max_retries = max_retries
            self.chat = self.ChatCompletions()
        
        class ChatCompletions:
            def create(self, model, messages, temperature=0.7, max_tokens=2000, stream=False):
                import requests
                import json
                
                # 构建请求头
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # 构建请求体
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream
                }
                
                try:
                    # 发送请求到 Ark API
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        if stream:
                            # 返回流式响应
                            return self._create_stream_response(response)
                        else:
                            # 返回普通响应
                            return self._create_response(response.json())
                    else:
                        # 如果 API 调用失败，返回模拟响应
                        print(f"Ark API 调用失败: {response.status_code} - {response.text}")
                        return self._create_mock_response(model, messages)
                        
                except Exception as e:
                    print(f"Ark API 调用异常: {e}")
                    return self._create_mock_response(model, messages)
            
            def _create_response(self, data):
                """创建标准响应对象"""
                return type('Response', (), {
                    'choices': [type('Choice', (), {
                        'message': type('Message', (), {
                            'content': data['choices'][0]['message']['content']
                        })()
                    })()]
                })()
            
            def _create_stream_response(self, response):
                """创建流式响应对象"""
                class StreamResponse:
                    def __iter__(self):
                        for line in response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    data = line[6:]
                                    if data != '[DONE]':
                                        try:
                                            chunk_data = json.loads(data)
                                            yield type('Chunk', (), {
                                                'choices': [type('Choice', (), {
                                                    'delta': type('Delta', (), {
                                                        'content': chunk_data['choices'][0]['delta'].get('content', '')
                                                    })()
                                                })()]
                                            })()
                                        except json.JSONDecodeError:
                                            continue
                return StreamResponse()
            
            def _create_mock_response(self, model, messages):
                """创建模拟响应"""
                user_message = messages[-1]['content'] if messages else "用户问题"
                return type('Response', (), {
                    'choices': [type('Choice', (), {
                        'message': type('Message', (), {
                            'content': f"基于您的问题，我为您提供以下专业分析：\n\n{user_message}\n\n请根据具体情况进行详细分析。"
                        })()
                    })()]
                })()

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
        
        # 强制设置 Ark 客户端编码
        self.ark_api_key = os.getenv("ARK_API_KEY") or "a40548ae-4aa0-4a7d-8a70-588ce0e563ed"
        self.ark_base_url = os.getenv("ARK_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3"
        if not self.ark_api_key or not self.ark_base_url:
            raise RuntimeError("请配置 ARK_API_KEY 和 ARK_BASE_URL 环境变量")
        self.ark_model = "doubao-1.5-pro-32k-250115"
        
        # 创建 Ark 客户端时强制设置编码
        try:
            print(f"🔧 Ark API 配置:")
            print(f"   Base URL: {self.ark_base_url}")
            print(f"   Model: {self.ark_model}")
            print(f"   API Key: {self.ark_api_key[:8]}..." if self.ark_api_key else "None")
            
            self.ark_client = Ark(
                api_key=self.ark_api_key, 
                base_url=self.ark_base_url,
                timeout=120,  # 使用与 FastAPI 相同的超时时间
                max_retries=2  # 使用与 FastAPI 相同的重试次数
            )
            print("✅ Ark 客户端初始化成功")
        except Exception as e:
            print(f"❌ Ark 客户端初始化失败: {e}")
            raise
    
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
            if ARK_AVAILABLE:
                # 使用用户提供的Ark配置
                self.llm_client = Ark(
                    api_key="a40548ae-4aa0-4a7d-8a70-588ce0e563ed",
                    base_url="https://ark.cn-beijing.volces.com/api/v3",
                    timeout=120,
                    max_retries=2
                )
                self.logger.info("LLM客户端初始化成功")
            else:
                self.logger.warning("volcenginesdkarkruntime模块不可用，使用模拟LLM客户端")
                self.llm_client = Ark()  # 使用模拟客户端
        except Exception as e:
            self.logger.error(f"LLM客户端初始化失败: {e}")
            self.llm_client = None
        
        print(f"Ark client: {self.llm_client}, ARK_AVAILABLE: {ARK_AVAILABLE}")
    
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
            if file_ext == '.txt':
                # 直接读取txt文件
                with open(contract_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents = [Document(page_content=content, metadata={"source": contract_file})]
            else:
                # 尝试使用Docx2txtLoader加载其他格式
                try:
                    loader = Docx2txtLoader(contract_file)
                    documents = loader.load()
                except ImportError:
                    raise ImportError("docx2txt模块未安装，请运行: pip install docx2txt")
                except Exception as e:
                    raise Exception(f"文档加载失败: {e}")
            
            if not documents:
                raise ValueError("文档加载失败，未获取到内容")
            
            # 分割文档
            if not self.text_splitter:
                raise RuntimeError("文本分割器未初始化")
            
            texts = self.text_splitter.split_documents(documents)
            self.logger.info(f"文档分割完成，共 {len(texts)} 个文本块")
            
            # 创建向量存储
            if self.embeddings:
                # 使用向量存储
                self.vector_store = Milvus.from_documents(
                    documents=texts,
                    embedding=self.embeddings,
                    collection_name=settings.MILVUS_COLLECTION_NAME,
                    connection_args=settings.milvus_connection_args
                )
                self.logger.info("向量存储创建成功")
            else:
                # 嵌入模型不可用时，使用简单的文本存储
                self.logger.warning("嵌入模型不可用，使用简单文本存储")
                self._simple_text_store = texts
                self.vector_store = None
            
            processing_time = time.time() - start_time
            self.logger.info(f"合同加载成功: {contract_file}, 处理时间: {processing_time:.2f}s")
            
            return True
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"合同加载失败: {contract_file}, 错误: {e}, 处理时间: {processing_time:.2f}s")
            log_error(e, {"contract_file": contract_file, "processing_time": processing_time})
            return False
    
    def _get_prompt_template(self, question: str) -> str:
        """
        根据问题类型选择合适的提示模板
        
        Args:
            question: 用户问题
            
        Returns:
            str: 格式化后的提示词字符串
        """
        question_lower = question.lower()
        
        # 根据问题类型选择合适的模板
        if any(keyword in question_lower for keyword in ["风险", "风险点", "风险分析"]):
            template = """请基于以下合同内容，对用户提出的风险相关问题进行专业分析：

合同内容：
{contract_content}

用户问题：{question}

请从以下方面进行专业分析：
1. 法律风险识别
2. 商业风险评估
3. 财务风险分析
4. 操作风险提示
5. 优化建议和应对措施

请提供客观、专业的分析，并给出实用的建议。"""
        elif any(keyword in question_lower for keyword in ["条款", "分析条款", "条款分析"]):
            template = """请基于以下合同内容，对用户提出的条款相关问题进行专业分析：

合同内容：
{contract_content}

用户问题：{question}

请从以下方面进行专业分析：
1. 条款含义解读
2. 权利义务分析
3. 潜在问题识别
4. 改进建议和优化方案

请提供清晰、准确的分析，并给出实用的建议。"""
        elif any(keyword in question_lower for keyword in ["法律", "法律建议", "法律问题"]):
            template = """请基于以下合同内容，对用户提出的法律相关问题提供专业建议：

合同内容：
{contract_content}

用户问题：{question}

请提供：
1. 相关法律依据
2. 法律风险评估
3. 合规建议措施
4. 重要注意事项

请提供专业、准确的法律建议，并注重实用性。"""
        elif any(keyword in question_lower for keyword in ["摘要", "总结", "概述"]):
            template = """请基于以下合同内容，对用户提出的总结相关问题进行专业分析：

合同内容：
{contract_content}

用户问题：{question}

请提供：
1. 合同类型和性质
2. 主要条款概述
3. 关键要点总结
4. 重要日期和期限
5. 风险提示和建议

请提供清晰、全面的总结，突出重点信息。"""
        elif any(keyword in question_lower for keyword in ["谈判", "协商", "建议"]):
            template = """请基于以下合同内容，对用户提出的谈判相关问题提供专业建议：

合同内容：
{contract_content}

用户问题：{question}

请提供：
1. 关键谈判要点
2. 可协商条款分析
3. 底线和让步空间
4. 谈判策略建议

请提供实用、可操作的谈判建议。"""
        else:
            template = """请基于以下合同内容，对用户提出的问题进行专业回答：

合同内容：
{contract_content}

用户问题：{question}

请提供专业、准确、有礼貌的回答，注重实用性和可操作性。"""
        
        # 格式化模板，使用当前加载的合同内容
        contract_content = getattr(self, 'contract_content', '暂无合同内容')
        if hasattr(self, '_simple_text_store') and self._simple_text_store:
            contract_content = "\n\n".join([doc.page_content for doc in self._simple_text_store[:3]])
        
        return template.format(
            contract_content=contract_content,
            question=question
        )
    
    def _retrieve_relevant_context(self, question: str, top_k: int = 5) -> str:
        """
        检索相关上下文
        
        Args:
            question: 用户问题
            top_k: 返回的相关文档数量
            
        Returns:
            str: 相关上下文
        """
        if self.vector_store:
            # 使用向量存储检索
            try:
                docs = self.vector_store.similarity_search(question, k=top_k)
                context = "\n\n".join([doc.page_content for doc in docs])
                return context
            except Exception as e:
                self.logger.error(f"向量检索失败: {e}")
                return "向量检索失败，使用简单文本匹配"
        elif hasattr(self, '_simple_text_store') and self._simple_text_store:
            # 使用简单文本存储
            try:
                # 简单的关键词匹配
                question_lower = question.lower()
                relevant_texts = []
                for doc in self._simple_text_store:
                    if any(keyword in doc.page_content.lower() for keyword in question_lower.split()):
                        relevant_texts.append(doc.page_content)
                
                if relevant_texts:
                    context = "\n\n".join(relevant_texts[:top_k])
                    return context
                else:
                    # 如果没有找到相关文本，返回前几个文档
                    context = "\n\n".join([doc.page_content for doc in self._simple_text_store[:top_k]])
                    return context
            except Exception as e:
                self.logger.error(f"简单文本检索失败: {e}")
                return "文本检索失败"
        else:
            return "暂无合同内容"
    
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
    
    def ensure_utf8(self, s):
        """确保字符串为 UTF-8 编码"""
        if isinstance(s, bytes):
            return s.decode('utf-8', errors='ignore')
        elif isinstance(s, str):
            try:
                # 尝试编码为 UTF-8，如果失败则重新编码
                s.encode('utf-8')
                return s
            except UnicodeEncodeError:
                return s.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        else:
            return str(s)

    def chat(self, question: str) -> str:
        """
        与合同审计助手对话
        
        Args:
            question: 用户问题
            
        Returns:
            str: 助手回复
        """
        try:
            # 获取相关上下文
            context = self._retrieve_relevant_context(question)
            # 获取格式化的提示模板
            prompt = self._get_prompt_template(question)
            
            # 强制确保所有字符串为 UTF-8
            prompt = self.ensure_utf8(prompt)
            question = self.ensure_utf8(question)
            
            # Debug 信息
            print(f"Debug - prompt type: {type(prompt)}, length: {len(prompt)}")
            print(f"Debug - question type: {type(question)}, length: {len(question)}")
            
            # 调用 Ark LLM
            print("🔄 正在调用 Ark LLM...")
            
            # 测试网络连接
            try:
                import urllib.request
                import urllib.parse
                import socket
                parsed_url = urllib.parse.urlparse(self.ark_base_url)
                host = parsed_url.netloc
                socket.create_connection((host, 443), timeout=5)
                print("✅ 网络连接正常")
            except Exception as e:
                print(f"⚠️ 网络连接测试失败: {e}")
                print("💡 请检查:")
                print("   1. 网络连接是否正常")
                print("   2. ARK_BASE_URL 是否正确")
                print("   3. 是否需要配置代理")
            
            # 使用与 FastAPI 相同的消息格式
            response = self.ark_client.chat.completions.create(
                model=self.ark_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的合同审计助手，具备丰富的法律和商业知识。请根据用户的具体问题，提供专业、准确、有礼貌的回答。在分析合同时，请注重客观性，提供实用的建议和见解。"},
                    {"role": "user", "content": prompt},
                ],
            )
            print("✅ Ark LLM 调用成功")
            
            result = response.choices[0].message.content
            return self.ensure_utf8(result)
            
        except Exception as e:
            print(f"❌ Ark LLM 调用详细错误: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Ark LLM 调用失败: {e}")
    
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

    def chat_stream(self, question: str, session_id: str = None):
        """
        Ark LLM 流式输出生成器，适用于 SSE/流式前端。
        无论输入什么，都只输出"请进一步明确审查方式"，支持持续对话。
        """
        import time
        import random
        
        # 发送开始事件
        yield {
            "event": "start",
            "timestamp": time.time(),
            "data": {
                "question": question,
                "status": "processing",
                "session_id": session_id,
                "role": "assistant",
                "extra_info": {
                    "model": getattr(self, 'ark_model', None),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        }
        
        # 模拟流式输出，逐字符输出
        response_text = "请进一步明确审查方式"
        for i, char in enumerate(response_text):
            # 添加随机延迟模拟真实流式输出
            time.sleep(random.uniform(0.05, 0.15))
            
            yield {
                "event": "token",
                "timestamp": time.time(),
                "data": {
                    "content": char,
                    "token_index": i + 1,
                    "is_final": False,
                    "session_id": session_id,
                    "role": "assistant",
                    "extra_info": {
                        "chunk_id": i + 1,
                        "content_length": 1,
                        "progress": f"{i + 1}/{len(response_text)}"
                    }
                }
            }
        
        # 发送完成事件
        yield {
            "event": "complete",
            "timestamp": time.time(),
            "data": {
                "total_tokens": len(response_text),
                "status": "success",
                "session_id": session_id,
                "role": "assistant",
                "is_final": True,
                "extra_info": {
                    "processing_time": 0,
                    "final_message": "流式输出完成",
                    "response_length": len(response_text)
                }
            }
        }

    def _real_llm_stream(self, question: str, session_id: str = None):
        """
        真实 Ark LLM 流式输出生成器，仅由 /chat/confirm 调用。
        """
        import time
        try:
            context = self._retrieve_relevant_context(question)
            prompt = self._get_prompt_template(question)
            prompt = self.ensure_utf8(prompt)
            question = self.ensure_utf8(question)

            # 发送上下文检索完成事件
            yield {
                "event": "context_ready",
                "timestamp": time.time(),
                "data": {
                    "context_length": len(context) if context else 0,
                    "prompt_length": len(prompt),
                    "session_id": session_id,
                    "role": "assistant",
                    "status": "context_ready",
                    "extra_info": {
                        "has_context": bool(context),
                        "context_preview": context[:100] + "..." if context and len(context) > 100 else context,
                        "phase": "real_llm"
                    }
                }
            }

            stream = self.ark_client.chat.completions.create(
                model=self.ark_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的合同审计助手，具备丰富的法律和商业知识。请根据用户的具体问题，提供专业、准确、有礼貌的回答。在分析合同时，请注重客观性，提供实用的建议和见解。"},
                    {"role": "user", "content": prompt},
                ],
                stream=True
            )
            token_count = 0
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = getattr(chunk.choices[0], "delta", None)
                if delta and getattr(delta, "content", None):
                    token_count += 1
                    content = self.ensure_utf8(delta.content)
                    yield {
                        "event": "token",
                        "timestamp": time.time(),
                        "data": {
                            "content": content,
                            "token_index": token_count,
                            "is_final": False,
                            "session_id": session_id,
                            "role": "assistant",
                            "extra_info": {
                                "chunk_id": token_count,
                                "content_length": len(content),
                                "phase": "real_llm"
                            }
                        }
                    }
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
                        "processing_time": 0,
                        "final_message": "流式输出完成",
                        "response_length": token_count,
                        "phase": "completed"
                    }
                }
            }
        except Exception as e:
            error_msg = f"[ERROR] Ark LLM 流式调用失败: {str(e)}"
            yield {
                "event": "error",
                "timestamp": time.time(),
                "data": {
                    "error": error_msg,
                    "status": "failed",
                    "session_id": session_id,
                    "role": "assistant",
                    "extra_info": {
                        "error_type": type(e).__name__,
                        "error_details": str(e),
                        "phase": "error"
                    }
                }
            }


# 全局聊天管理器实例（延迟初始化）
_chat_manager = None

def get_chat_manager():
    """获取聊天管理器实例（单例模式）"""
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = ContractChatManager()
    return _chat_manager

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    合同审计聊天系统                           ║
║                    Contract Audit Chat                       ║
║                                                              ║
║  企业级版本 - 支持LangChain、向量存储、智能对话等功能        ║
║  输入 'help' 查看帮助，输入 'quit' 退出                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_help():
    """打印帮助信息"""
    help_text = """
📋 可用命令：
• help                    - 显示此帮助信息
• load <文件路径>         - 加载合同文件到向量存储
• new                     - 创建新会话
• list                    - 列出所有会话
• stats                   - 显示系统统计
• history <会话ID>        - 查看会话历史
• cleanup                 - 清理过期会话
• quit/exit               - 退出程序

可以直接输入问题即可开始聊天，例如：
• "这个合同有什么风险点？"
• "分析一下付款条款"
• "请总结合同主要内容"
• "这个条款有什么法律问题？"

🔧 示例操作：
1. 输入: load sample_contract.docx
2. 输入: new
3. 输入: "请分析这个合同的风险点"

⚙️  系统特性：
• 支持多种文档格式 (.docx, .doc, .pdf, .txt)
• 智能向量检索和上下文理解
• 多用户会话管理
• 自动过期会话清理
• 详细的性能监控和日志记录
"""
    print(help_text)

def interactive_chat():
    """交互式聊天界面"""
    print_banner()
    
    # 获取聊天管理器实例
    chat_manager = get_chat_manager()
    
    # 自动加载示例合同文件（如果存在）
    sample_file = "sample_contract.txt"
    if os.path.exists(sample_file):
        print(f"📄 自动加载示例合同文件: {sample_file}")
        if chat_manager.load_contract_to_vectorstore(sample_file):
            print("✅ 示例合同加载成功")
        else:
            print("❌ 示例合同加载失败")
    else:
        print("📄 未找到示例合同文件，您可以稍后使用 'load <文件路径>' 命令加载")
    
    # 创建默认会话
    current_user_id = "default_user"
    current_session_id = chat_manager.create_session(current_user_id)
    print(f"✅ 默认会话已创建: {current_session_id}")
    print()
    
    print_help()
    print()
    
    while True:
        try:
            user_input = input("\n🤖 请输入命令或问题: ").strip()
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 感谢使用合同审计聊天系统，再见！")
                break
            
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            elif user_input.lower().startswith('load '):
                file_path = user_input[5:].strip()
                if chat_manager.load_contract_to_vectorstore(file_path):
                    print(f"✅ 合同文件加载成功: {file_path}")
                else:
                    print(f"❌ 合同文件加载失败: {file_path}")
                continue
            
            elif user_input.lower() == 'new':
                current_session_id = chat_manager.create_session(current_user_id)
                print(f"✅ 新会话已创建: {current_session_id}")
                continue
            
            elif user_input.lower() == 'list':
                sessions = chat_manager.list_sessions(current_user_id)
                if sessions:
                    print("\n📋 当前会话列表:")
                    for i, session in enumerate(sessions, 1):
                        print(f"  {i}. 会话ID: {session['session_id'][:8]}...")
                        print(f"     创建时间: {session['created_at']}")
                        print(f"     消息数量: {session['message_count']}")
                        print(f"     合同文件: {session['contract_file'] or '无'}")
                        print()
                else:
                    print("📭 暂无会话")
                continue
            
            elif user_input.lower() == 'stats':
                stats = chat_manager.get_system_stats()
                print("\n📊 系统统计信息:")
                print(f"  总会话数: {stats['total_sessions']}")
                print(f"  总消息数: {stats['total_messages']}")
                print(f"  活跃用户数: {stats['active_users']}")
                print(f"  向量存储: {'✅' if stats['vector_store_available'] else '❌'}")
                print(f"  LLM客户端: {'✅' if stats['llm_client_available'] else '❌'}")
                print(f"  嵌入模型: {'✅' if stats['embeddings_available'] else '❌'}")
                print(f"  Ark服务: {'✅' if stats['ark_available'] else '❌'}")
                
                if stats['user_stats']:
                    print("\n👥 用户统计:")
                    for user_id, user_stat in stats['user_stats'].items():
                        print(f"  用户 {user_id}: {user_stat['sessions']} 个会话, {user_stat['messages']} 条消息")
                continue
            
            elif user_input.lower() == 'cleanup':
                cleaned_count = chat_manager.cleanup_expired_sessions()
                print(f"🧹 清理了 {cleaned_count} 个过期会话")
                continue
            
            elif user_input.lower().startswith('history '):
                session_id = user_input[8:].strip()
                history = chat_manager.get_session_history(session_id)
                if history:
                    print(f"\n📜 会话历史 (ID: {session_id}):")
                    for i, msg in enumerate(history['messages'], 1):
                        role = "👤 用户" if msg['role'] == 'user' else "🤖 助手"
                        print(f"  {i}. {role}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
                else:
                    print(f"❌ 未找到会话: {session_id}")
                continue
            
            # 处理聊天消息
            if not current_session_id:
                print("⚠️  请先创建会话 (输入 'new') 或加载合同文件 (输入 'load <文件路径>')")
                continue
            
            # 发送聊天消息
            print("🤔 正在处理您的问题...")
            start_time = time.time()
            # 流式输出
            for token in chat_manager.chat_stream(user_input):
                print(token, end="", flush=True)
            response_time = time.time() - start_time
            print()  # 换行
            print(f"🤖 回复 (响应时间: {response_time:.2f}s)")
            print()
            # 显示会话信息
            print(f"[会话: {current_session_id[:8]}...] [用户: {current_user_id}] [消息数: {len(chat_manager.get_session(current_session_id).messages) if chat_manager.get_session(current_session_id) else 0}]")
            print()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  检测到中断信号，输入 'quit' 退出程序")
        except Exception as e:
            print(f"❌ 发生错误: {e}")

def create_sample_contract():
    """创建示例合同文件"""
    sample_content = """
合同示例

甲方：示例公司A
乙方：示例公司B

第一条 合同目的
本合同的目的是为了规范双方在项目合作中的权利义务关系。

第二条 合作内容
1. 甲方负责提供技术支持
2. 乙方负责提供资金支持
3. 双方共同承担项目风险

第三条 付款条款
1. 乙方应在合同签订后30日内支付首付款50万元
2. 项目完成后支付剩余款项
3. 逾期付款按日利率0.05%计算违约金

第四条 违约责任
1. 任何一方违约应承担违约责任
2. 违约金为合同总额的20%
3. 造成损失的应承担赔偿责任

第五条 争议解决
因本合同引起的争议，双方应友好协商解决；协商不成的，提交仲裁机构仲裁。

第六条 其他
1. 本合同自双方签字盖章之日起生效
2. 本合同一式两份，双方各执一份
3. 未尽事宜，双方可另行协商

甲方（盖章）：示例公司A
乙方（盖章）：示例公司B
签订日期：2024年1月1日
"""
    
    sample_file = "sample_contract.txt"
    try:
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        print(f"✅ 示例合同文件已创建: {sample_file}")
        return sample_file
    except Exception as e:
        print(f"❌ 创建示例合同文件失败: {e}")
        return None

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("合同审计聊天系统 (企业级版本)")
            print("用法: python chat.py [选项]")
            print("选项:")
            print("  --help, -h    显示帮助信息")
            print("  --sample      创建示例合同文件")
            print("  --demo        运行演示模式")
            return
        elif sys.argv[1] == '--sample':
            create_sample_contract()
            return
        elif sys.argv[1] == '--demo':
            # 演示模式
            print("🎭 启动演示模式...")
            sample_file = create_sample_contract()
            if sample_file:
                chat_manager = get_chat_manager()
                chat_manager.load_contract_to_vectorstore(sample_file)
                session_id = chat_manager.create_session("demo_user")
                print(f"✅ 演示会话已创建: {session_id}")
                
                # 演示问题
                demo_questions = [
                    "请总结这个合同的主要内容",
                    "这个合同有什么风险点？",
                    "分析一下付款条款",
                    "违约责任条款有什么问题？"
                ]
                
                for question in demo_questions:
                    print(f"\n🤔 演示问题: {question}")
                    result = chat_manager.chat(question)
                    print(f"🤖 回复: {result[:200]}...")
                    print("-" * 50)
                
                print("\n🎉 演示完成！您可以继续使用交互式聊天界面。")
            
            interactive_chat()
            return
    
    # 默认启动交互式聊天
    interactive_chat()

if __name__ == "__main__":
    main()
