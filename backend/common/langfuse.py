"""
Langfuse 集成模块 - 支持开关控制
"""
import logging
from typing import Optional
from langfuse import get_client
from langfuse.langchain import CallbackHandler
from common.config import config

logger = logging.getLogger(__name__)

class LangfuseManager:
    """Langfuse管理器（单例）"""
    _instance = None
    _client = None
    _handler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_client(self):
        """获取Langfuse客户端"""
        if not config.LANGFUSE_TRACING:
            return None

        if self._client is None:
            if not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
                logger.warning("⚠️ Langfuse enabled but missing credentials")
                return None

            try:
                self._client = get_client(
                    public_key=config.LANGFUSE_PUBLIC_KEY,
                    secret_key=config.LANGFUSE_SECRET_KEY,
                    host=config.LANGFUSE_HOST,
                )
                if self._client.auth_check():
                    logger.info("✅ Langfuse client ready")
                else:
                    logger.warning("⚠️ Langfuse auth failed")
                    self._client = None
            except Exception as e:
                logger.error(f"❌ Langfuse init failed: {e}")
                self._client = None

        return self._client

    def get_handler(self):
        """获取CallbackHandler"""
        if not config.LANGFUSE_TRACING:
            return None

        if self._handler is None:
            # 验证凭证
            if not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
                logger.warning("⚠️ Langfuse enabled but missing credentials")
                return None

            try:
                self._handler = CallbackHandler()
                logger.info("✅ Langfuse handler ready")
            except Exception as e:
                logger.error(f"❌ Langfuse handler init failed: {e}")
                self._handler = None

        return self._handler

# 全局管理器实例
_manager = LangfuseManager()

# 函数式API（推荐新代码使用）
def get_langfuse_client() -> Optional:
    """获取Langfuse客户端"""
    return _manager.get_client()

def get_langfuse_handler() -> Optional:
    """获取Langfuse handler"""
    return _manager.get_handler()

# 向后兼容：模块级变量（延迟求值）
class _LazyHandler:
    """延迟求值的handler包装器"""
    def __call__(self):
        return get_langfuse_handler()

    def __repr__(self):
        result = get_langfuse_handler()
        return f"<LangfuseHandler: {result}>"

langfuse = get_langfuse_client
langfuse_handler = _LazyHandler()
