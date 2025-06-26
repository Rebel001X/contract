"""
合同审计系统日志模块
企业级日志管理，支持结构化日志和多种输出格式
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from ContractAudit.config import settings


class ContractAuditLogger:
    """
    合同审计系统日志管理器
    提供统一的日志接口和配置
    """
    
    def __init__(self):
        """初始化日志管理器"""
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志配置"""
        # 移除默认的日志处理器
        logger.remove()
        
        # 创建日志目录
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 控制台输出格式
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # 文件输出格式（结构化JSON）
        file_format = (
            '{"time": "{time:YYYY-MM-DD HH:mm:ss}", '
            '"level": "{level}", '
            '"name": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}", '
            '"extra": {extra}'
            '}'
        )
        
        # 添加控制台处理器
        logger.add(
            sys.stdout,
            format=console_format,
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # 添加文件处理器
        logger.add(
            settings.LOG_FILE,
            format=file_format,
            level=settings.LOG_LEVEL,
            rotation="100 MB",  # 文件大小达到100MB时轮转
            retention="30 days",  # 保留30天的日志
            compression="zip",  # 压缩旧日志
            backtrace=True,
            diagnose=True,
            enqueue=True  # 异步写入
        )
        
        # 添加错误日志文件
        error_log_file = log_dir / "error.log"
        logger.add(
            error_log_file,
            format=file_format,
            level="ERROR",
            rotation="50 MB",
            retention="60 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True
        )
        
        # 添加访问日志文件
        access_log_file = log_dir / "access.log"
        logger.add(
            access_log_file,
            format=file_format,
            level="INFO",
            filter=lambda record: record["extra"].get("log_type") == "access",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            enqueue=True
        )
    
    def get_logger(self, name: str = "ContractAudit"):
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            loguru.Logger: 配置好的日志记录器
        """
        return logger.bind(name=name)
    
    def log_api_request(self, method: str, path: str, status_code: int, 
                       duration: float, user_id: Optional[str] = None):
        """
        记录API请求日志
        
        Args:
            method: HTTP方法
            path: 请求路径
            status_code: 响应状态码
            duration: 请求处理时间（秒）
            user_id: 用户ID
        """
        extra_data = {
            "log_type": "access",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": duration,
            "user_id": user_id
        }
        
        level = "ERROR" if status_code >= 400 else "INFO"
        logger.bind(**extra_data).log(
            level,
            f"API Request: {method} {path} - {status_code} ({duration:.3f}s)"
        )
    
    def log_chat_interaction(self, session_id: str, user_id: str, 
                           message_type: str, message_length: int,
                           response_time: float, success: bool):
        """
        记录聊天交互日志
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            message_type: 消息类型（user/assistant）
            message_length: 消息长度
            response_time: 响应时间（秒）
            success: 是否成功
        """
        extra_data = {
            "log_type": "chat",
            "session_id": session_id,
            "user_id": user_id,
            "message_type": message_type,
            "message_length": message_length,
            "response_time": response_time,
            "success": success
        }
        
        level = "ERROR" if not success else "INFO"
        logger.bind(**extra_data).log(
            level,
            f"Chat Interaction: {session_id} - {message_type} ({message_length} chars, {response_time:.3f}s)"
        )
    
    def log_contract_processing(self, contract_file: str, file_size: int,
                              processing_time: float, success: bool,
                              error_message: Optional[str] = None):
        """
        记录合同处理日志
        
        Args:
            contract_file: 合同文件路径
            file_size: 文件大小（字节）
            processing_time: 处理时间（秒）
            success: 是否成功
            error_message: 错误信息
        """
        extra_data = {
            "log_type": "contract",
            "contract_file": contract_file,
            "file_size": file_size,
            "processing_time": processing_time,
            "success": success,
            "error_message": error_message
        }
        
        level = "ERROR" if not success else "INFO"
        logger.bind(**extra_data).log(
            level,
            f"Contract Processing: {contract_file} ({file_size} bytes, {processing_time:.3f}s)"
        )
    
    def log_system_event(self, event_type: str, event_data: Dict[str, Any],
                        level: str = "INFO"):
        """
        记录系统事件日志
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            level: 日志级别
        """
        extra_data = {
            "log_type": "system",
            "event_type": event_type,
            **event_data
        }
        
        logger.bind(**extra_data).log(
            level,
            f"System Event: {event_type}"
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        记录错误日志
        
        Args:
            error: 异常对象
            context: 上下文信息
        """
        extra_data = {
            "log_type": "error",
            "error_type": type(error).__name__,
            "context": context or {}
        }
        
        logger.bind(**extra_data).exception(
            f"Error: {str(error)}"
        )
    
    def log_performance(self, operation: str, duration: float, 
                       metadata: Optional[Dict[str, Any]] = None):
        """
        记录性能日志
        
        Args:
            operation: 操作名称
            duration: 执行时间（秒）
            metadata: 元数据
        """
        extra_data = {
            "log_type": "performance",
            "operation": operation,
            "duration": duration,
            "metadata": metadata or {}
        }
        
        level = "WARNING" if duration > 5.0 else "INFO"
        logger.bind(**extra_data).log(
            level,
            f"Performance: {operation} - {duration:.3f}s"
        )


# 全局日志管理器实例
contract_logger = ContractAuditLogger()


def get_logger(name: str = "ContractAudit"):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        loguru.Logger: 配置好的日志记录器
    """
    return contract_logger.get_logger(name)


# 便捷函数
def log_api_request(method: str, path: str, status_code: int, 
                   duration: float, user_id: Optional[str] = None):
    """记录API请求日志"""
    contract_logger.log_api_request(method, path, status_code, duration, user_id)


def log_chat_interaction(session_id: str, user_id: str, 
                        message_type: str, message_length: int,
                        response_time: float, success: bool):
    """记录聊天交互日志"""
    contract_logger.log_chat_interaction(
        session_id, user_id, message_type, message_length, 
        response_time, success
    )


def log_contract_processing(contract_file: str, file_size: int,
                          processing_time: float, success: bool,
                          error_message: Optional[str] = None):
    """记录合同处理日志"""
    contract_logger.log_contract_processing(
        contract_file, file_size, processing_time, success, error_message
    )


def log_system_event(event_type: str, event_data: Dict[str, Any],
                    level: str = "INFO"):
    """记录系统事件日志"""
    contract_logger.log_system_event(event_type, event_data, level)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """记录错误日志"""
    contract_logger.log_error(error, context)


def log_performance(operation: str, duration: float, 
                   metadata: Optional[Dict[str, Any]] = None):
    """记录性能日志"""
    contract_logger.log_performance(operation, duration, metadata)


# 日志装饰器
def log_function_call(func):
    """
    函数调用日志装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = logger.bind().info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.bind().info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.bind().exception(f"Error in {func.__name__}: {str(e)}")
            raise
    
    return wrapper


def log_performance_metric(func):
    """
    性能指标日志装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    import time
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            log_performance(func.__name__, duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            log_performance(func.__name__, duration, {"error": str(e)})
            raise
    
    return wrapper 