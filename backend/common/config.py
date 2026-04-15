"""
通用配置模块
集中管理所有配置和 API Key
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置"""

    # API 配置
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "")

    # LangSmith 配置
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "langchain-learning")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")

    # Langfuse 配置
    LANGFUSE_TRACING: bool = os.getenv("LANGFUSE_TRACING", "false").lower() == "true"
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # 应用配置
    APP_NAME: str = "IChat"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CORS 配置
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


# 全局配置实例
config = Config()
