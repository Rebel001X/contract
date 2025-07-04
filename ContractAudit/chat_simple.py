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

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    合同审计聊天系统                           ║
║                    Contract Audit Chat                       ║
║                                                              ║
║  简化版本 - 支持合同分析、风险评估、法律建议等功能            ║
║  输入 'help' 查看帮助，输入 'quit' 退出                      ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_help():
    """打印帮助信息"""
    help_text = """
📋 可用命令：
• help                    - 显示此帮助信息
• load <文件路径>         - 加载合同文件（支持 .txt 文件）
• new                     - 创建新会话
• list                    - 列出所有会话
• stats                   - 显示系统统计
• history <会话ID>        - 查看会话历史
• quit/exit               - 退出程序

💬 直接输入问题即可开始聊天，例如：
• "这个合同有什么风险点？"
• "分析一下付款条款"
• "请总结合同主要内容"
• "这个条款有什么法律问题？"

🔧 示例操作：
1. 输入: load sample_contract.txt
2. 输入: new
3. 输入: "请分析这个合同的风险点"
"""
    print(help_text)

def interactive_chat():
    """交互式聊天界面"""
    print_banner()
    
    current_session_id = None
    current_user_id = "default_user"
    
    while True:
        try:
            # 显示当前状态
            if current_session_id:
                session = chat_manager.get_session(current_session_id)
                if session:
                    print(f"\n[会话: {current_session_id[:8]}...] [用户: {current_user_id}] [消息数: {session.get_message_count()}]")
                else:
                    current_session_id = None
            
            # 获取用户输入
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
            result = chat_manager.chat(current_session_id, user_input)
            
            if result.get('error'):
                print(f"❌ 错误: {result['response']}")
            else:
                print(f"\n🤖 回复 (响应时间: {result['response_time']:.2f}s):")
                print(f"{result['response']}")
                
                if result.get('context_used'):
                    print(f"\n📄 使用的上下文: {result['context_used']}")
        
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
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("合同审计聊天系统")
            print("用法: python chat_simple.py [选项]")
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
                    result = chat_manager.chat(session_id, question)
                    print(f"🤖 回复: {result['response'][:200]}...")
                    print("-" * 50)
                
                print("\n🎉 演示完成！您可以继续使用交互式聊天界面。")
            
            interactive_chat()
            return
    
    # 默认启动交互式聊天
    interactive_chat()

if __name__ == "__main__":
    main() 