"""
合同审计系统配置文件
企业级配置管理，支持多环境部署
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    """
    系统配置类
    使用Pydantic进行配置验证和管理
    """
    
    # 应用基础配置
    APP_NAME: str = Field(default="ContractAudit", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=False, description="调试模式")
    ENVIRONMENT: str = Field(default="production", description="运行环境")
    
    # 服务配置
    HOST: str = Field(default="0.0.0.0", description="服务监听地址")
    PORT: int = Field(default=8010, description="服务监听端口")
    
    # 数据库配置（已删除 Milvus）
    # MILVUS_HOST: str = Field(default="localhost", description="Milvus向量数据库主机")
    # MILVUS_PORT: str = Field(default="19530", description="Milvus向量数据库端口")
    # MILVUS_COLLECTION_NAME: str = Field(default="contract_vectors", description="Milvus集合名称")
    # MILVUS_VECTOR_DIM: int = Field(default=384, description="向量维度")
    
    # LLM服务配置（已删除）
    # ARK_API_KEY: str = Field(default="", description="火山引擎Ark API密钥")
    # ARK_BASE_URL: str = Field(default="https://ark.cn-beijing.volces.com/api/v3", description="Ark服务基础URL")
    # ARK_TIMEOUT: int = Field(default=120, description="Ark API超时时间(秒)")
    # ARK_MAX_RETRIES: int = Field(default=3, description="Ark API最大重试次数")
    
    # 嵌入模型配置（已删除）
    # EMBEDDING_MODEL_NAME: str = Field(
    #     default="sentence-transformers/all-MiniLM-L6-v2", 
    #     description="嵌入模型名称"
    # )
    # EMBEDDING_DEVICE: str = Field(default="cpu", description="嵌入模型运行设备")
    
    # 文档处理配置（已删除）
    # CHUNK_SIZE: int = Field(default=1000, description="文档分块大小")
    # CHUNK_OVERLAP: int = Field(default=200, description="文档分块重叠大小")
    # MAX_DOCUMENT_SIZE: int = Field(default=50 * 1024 * 1024, description="最大文档大小(字节)")
    
    # 会话管理配置
    MAX_SESSIONS_PER_USER: int = Field(default=10, description="每个用户最大会话数")
    SESSION_TIMEOUT_HOURS: int = Field(default=24, description="会话超时时间(小时)")
    MAX_MESSAGES_PER_SESSION: int = Field(default=100, description="每个会话最大消息数")
    
    # 安全配置
    SECRET_KEY: str = Field(default="", description="应用密钥")
    ALLOWED_ORIGINS: list = Field(default=["*"], description="允许的跨域来源")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="logs/contract_audit.log", description="日志文件路径")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    # 文件存储配置
    UPLOAD_DIR: str = Field(default="uploads", description="文件上传目录")
    TEMP_DIR: str = Field(default="temp", description="临时文件目录")
    ALLOWED_FILE_TYPES: list = Field(
        default=[".docx", ".doc", ".pdf", ".txt"],
        description="允许的文件类型"
    )
    
    # 缓存配置
    CACHE_TTL: int = Field(default=3600, description="缓存生存时间(秒)")
    CACHE_MAX_SIZE: int = Field(default=1000, description="缓存最大条目数")
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, description="启用指标监控")
    METRICS_PORT: int = Field(default=8002, description="指标服务端口")
    
    # 数据库连接URL
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:Kd123%40%23%24qwer@172.18.53.39:3306/smart_contract?charset=utf8mb4",
        description="SQLAlchemy数据库连接URL"
    )
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的字段
    
    def __init__(self, **kwargs):
        """初始化配置"""
        super().__init__(**kwargs)
        self._validate_config()
        self._create_directories()
    
    def _validate_config(self):
        """验证配置有效性"""
        # 已删除 ARK_API_KEY 相关验证
        
        if not self.SECRET_KEY:
            print("警告: SECRET_KEY未设置，建议在生产环境中设置")
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.UPLOAD_DIR,
            self.TEMP_DIR,
            os.path.dirname(self.LOG_FILE)
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 已删除 milvus_connection_args 和 ark_client_config 方法


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置实例
    用于依赖注入
    """
    return settings


# 环境变量配置示例
ENV_EXAMPLE = """
# 应用配置
APP_NAME=ContractAudit
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# 服务配置
HOST=0.0.0.0
PORT=8010

# 数据库配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=contract_vectors
MILVUS_VECTOR_DIM=384

# LLM服务配置
ARK_API_KEY=your_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_TIMEOUT=120
ARK_MAX_RETRIES=3

# 嵌入模型配置
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# 文档处理配置
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_DOCUMENT_SIZE=52428800

# 会话管理配置
MAX_SESSIONS_PER_USER=10
SESSION_TIMEOUT_HOURS=24
MAX_MESSAGES_PER_SESSION=100

# 安全配置
SECRET_KEY=your_secret_key_here
ALLOWED_ORIGINS=["*"]
RATE_LIMIT_PER_MINUTE=60

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/contract_audit.log

# 文件存储配置
UPLOAD_DIR=uploads
TEMP_DIR=temp
ALLOWED_FILE_TYPES=[".docx", ".doc", ".pdf", ".txt"]

# 缓存配置
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=8002
"""

# SQLAlchemy数据库引擎和Session
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

# 设置数据库连接时区
@event.listens_for(engine, "connect")
def set_timezone(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET time_zone = '+08:00'")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_engine():
    return engine

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
