"""
合同审计对话功能模块
简化的聊天管理系统，支持多用户会话
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# 强制设置环境变量
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# 确保 Python3 默认编码为 UTF-8
if hasattr(sys, 'setdefaultencoding'):
    sys.setdefaultencoding('utf-8')

print("系统默认编码:", sys.getdefaultencoding())
print("环境变量 PYTHONIOENCODING:", os.environ.get("PYTHONIOENCODING"))

# 尝试导入配置和日志模块，如果不可用则使用默认配置
try:
    from ContractAudit.config import settings
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
    
    settings = Settings()

def get_logger(name):
    """简单的日志函数"""
    def log(level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [{name}] {message}")
    return log

def log_performance_metric(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数 {func.__name__} 执行时间: {end_time - start_time:.2f}秒")
        return result
    return wrapper

def log_error(error, context=None):
    """错误日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [ERROR] {error}")
    if context:
        print(f"[{timestamp}] [CONTEXT] {context}")

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
    合同审计聊天管理器
    管理所有聊天会话，提供会话创建、消息处理等功能
    """
    
    def __init__(self):
        """初始化聊天管理器"""
        self.sessions: Dict[str, ChatSession] = {}
        self.logger = get_logger("ContractChatManager")
        self._initialize_components()
        self.logger("INFO", "合同审计聊天管理器初始化完成")

    def _initialize_components(self):
        """初始化组件"""
        try:
            # 创建必要的目录
            os.makedirs("uploads", exist_ok=True)
            os.makedirs("temp", exist_ok=True)
            os.makedirs("logs", exist_ok=True)
            self.logger("INFO", "目录结构初始化完成")
        except Exception as e:
            self.logger("ERROR", f"目录初始化失败: {e}")

    @log_performance_metric
    def create_session(self, user_id: str, contract_file: Optional[str] = None) -> str:
        """
        创建新的聊天会话
        
        Args:
            user_id: 用户ID
            contract_file: 合同文件路径（可选）
            
        Returns:
            str: 会话ID
        """
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            contract_file=contract_file
        )
        self.sessions[session_id] = session
        self.logger("INFO", f"创建新会话: {session_id}, 用户: {user_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        获取会话对象
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[ChatSession]: 会话对象，如果不存在则返回None
        """
        return self.sessions.get(session_id)

    def _is_session_expired(self, session: ChatSession) -> bool:
        """
        检查会话是否过期
        
        Args:
            session: 会话对象
            
        Returns:
            bool: 是否过期
        """
        if not session.updated_at:
            return True
        
        timeout_hours = getattr(settings, 'SESSION_TIMEOUT_HOURS', 24)
        timeout_seconds = timeout_hours * 3600
        time_diff = (datetime.now() - session.updated_at).total_seconds()
        
        return time_diff > timeout_seconds

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger("INFO", f"删除会话: {session_id}")
            return True
        return False

    def load_contract_to_vectorstore(self, contract_file: str) -> bool:
        """
        加载合同文件（简化版本）
        
        Args:
            contract_file: 合同文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            # 简化的文件加载逻辑
            if os.path.exists(contract_file):
                self.logger("INFO", f"合同文件加载成功: {contract_file}")
                return True
            else:
                self.logger("ERROR", f"合同文件不存在: {contract_file}")
                return False
        except Exception as e:
            self.logger("ERROR", f"合同文件加载失败: {e}")
            return False

    def chat(self, question: str, session_id: str = None) -> str:
        """
        处理聊天消息（简化版本）
        
        Args:
            question: 用户问题
            session_id: 会话ID（可选）
            
        Returns:
            str: 回复内容
        """
        try:
            # 简化的回复逻辑
            response = f"收到您的问题: {question}\n\n这是一个简化的回复，实际应用中需要集成大模型服务。"
            
            # 如果提供了会话ID，添加到会话历史
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                session.add_message("user", question)
                session.add_message("assistant", response)
            
            return response
        except Exception as e:
            error_msg = f"聊天处理失败: {e}"
            self.logger("ERROR", error_msg)
            return error_msg

    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 会话历史信息
        """
        session = self.get_session(session_id)
        if session:
            return session.to_dict()
        return None

    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出会话
        
        Args:
            user_id: 用户ID（可选，用于过滤）
            
        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        sessions = []
        for session in self.sessions.values():
            if user_id is None or session.user_id == user_id:
                sessions.append(session.to_dict())
        return sessions

    def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话
        
        Returns:
            int: 清理的会话数量
        """
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self.logger("INFO", f"清理了 {len(expired_sessions)} 个过期会话")
        
        return len(expired_sessions)

    def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            Dict[str, Any]: 系统统计信息
        """
        total_sessions = len(self.sessions)
        total_messages = sum(len(session.messages) for session in self.sessions.values())
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "active_sessions": total_sessions,
            "system_status": "running"
        }

    def chat_stream(self, question: str, session_id: str = None):


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
            time.sleep(0.1)

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
        try:
            # 简化的流式回复
            response = f"收到您的问题: {question}\n\n这是一个简化的流式回复。"

            # 模拟流式输出
            for char in response:
                yield char
                time.sleep(0.01)  # 模拟延迟

        except Exception as e:
            error_msg = f"流式聊天处理失败: {e}"
            self.logger("ERROR", error_msg)
            yield error_msg
        """


# 全局聊天管理器实例
_chat_manager = None

def get_chat_manager() -> ContractChatManager:
    """
    获取聊天管理器实例（单例模式）
    
    Returns:
        ContractChatManager: 聊天管理器实例
    """
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = ContractChatManager()
    return _chat_manager

def print_banner():
    """打印系统横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    合同审计聊天系统                            ║
    ║                    Contract Audit Chat                       ║
    ║                                                              ║
    ║  版本: 1.0.0                                                 ║
    ║  状态: 简化模式 (无大模型集成)                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_help():
    """打印帮助信息"""
    help_text = """
    可用命令:
    - /help: 显示此帮助信息
    - /sessions: 显示所有会话
    - /stats: 显示系统统计
    - /clear: 清理过期会话
    - /quit 或 /exit: 退出系统
    
    聊天功能:
    - 直接输入消息进行对话
    - 系统会返回简化的回复
    """
    print(help_text)

def interactive_chat():
    """交互式聊天界面"""
    print_banner()
    print_help()
    
    chat_manager = get_chat_manager()
    session_id = chat_manager.create_session("interactive_user")
    
    print(f"\n会话已创建: {session_id}")
    print("开始聊天 (输入 /help 查看帮助):\n")
    
    while True:
        try:
            user_input = input("用户: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['/quit', '/exit']:
                print("再见!")
                break
            elif user_input.lower() == '/help':
                print_help()
                continue
            elif user_input.lower() == '/sessions':
                sessions = chat_manager.list_sessions()
                print(f"当前会话数: {len(sessions)}")
                for session in sessions:
                    print(f"  - {session['session_id']}: {session['message_count']} 条消息")
                continue
            elif user_input.lower() == '/stats':
                stats = chat_manager.get_system_stats()
                print(f"系统统计: {stats}")
                continue
            elif user_input.lower() == '/clear':
                cleaned = chat_manager.cleanup_expired_sessions()
                print(f"清理了 {cleaned} 个过期会话")
                continue
            
            # 处理聊天消息
            response = chat_manager.chat(user_input, session_id)
            print(f"助手: {response}\n")
            
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")

def create_sample_contract():
    """创建示例合同文件"""
    sample_content = """
    合同示例
    
    甲方：示例公司
    乙方：示例个人
    
    第一条 合同目的
    本合同旨在规范双方的权利义务关系。
    
    第二条 合同期限
    本合同自签订之日起生效，有效期为一年。
    
    第三条 违约责任
    任何一方违反本合同约定，应承担相应的违约责任。
    """
    
    contract_file = "sample_contract.txt"
    with open(contract_file, "w", encoding="utf-8") as f:
        f.write(sample_content)
    
    print(f"示例合同文件已创建: {contract_file}")
    return contract_file

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-sample":
            create_sample_contract()
        elif sys.argv[1] == "help":
            print_help()
        else:
            print("未知命令。使用 'python chat.py help' 查看帮助。")
    else:
        interactive_chat()

if __name__ == "__main__":
    main()

