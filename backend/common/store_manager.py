"""
Store 管理器 - 统一管理 LangGraph Store 用于长期记忆
"""
import pathlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StoreManager:
    """Store 管理器 - 负责创建和管理长期记忆存储"""

    def __init__(self, store_backend: str = "sqlite"):
        """
        初始化 Store 管理器

        Args:
            store_backend: 存储后端类型 ("memory" 或 "sqlite"，默认 "sqlite")
        """
        self._store_backend = store_backend
        self._store = None
        self._conn = None  # 保存 aiosqlite 连接引用
        logger.info(f"📦 [StoreManager] 初始化完成，后端: {store_backend}")

    async def get_store(self):
        """
        获取 Store 实例

        Returns:
            Store 实例（InMemoryStore 或 AsyncSqliteStore）
        """
        if self._store is None:
            self._store = await self._create_store(self._store_backend)
            logger.info(f"✅ [StoreManager] Store 已创建: {type(self._store).__name__}")
        return self._store

    async def reset_store(self):
        """
        重置 Store 实例（用于测试或重新初始化）
        """
        await self.close()
        self._store = None
        logger.info("📦 [StoreManager] Store 已重置")

    async def _create_store(self, backend: str):
        """
        异步创建 Store 实例

        Args:
            backend: 存储后端类型

        Returns:
            Store 实例
        """
        if backend == "memory":
            from langgraph.store.memory import InMemoryStore
            return InMemoryStore()
        elif backend == "sqlite":
            import aiosqlite
            from langgraph.store.sqlite.aio import AsyncSqliteStore

            db_path = pathlib.Path("data/deepagent_demo.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建异步 SQLite 连接
            self._conn = await aiosqlite.connect(str(db_path))

            # 创建 Store 实例
            store = AsyncSqliteStore(conn=self._conn)

            # 初始化表结构
            await store.setup()

            # 显式提交 setup 的事务
            await self._conn.commit()

            logger.info(f"✅ [StoreManager] AsyncSqliteStore 已初始化: {db_path}")
            return store
        else:
            raise ValueError(f"Unknown store backend: {backend}")

    async def close(self):
        """关闭 Store 连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("📦 [StoreManager] Store 连接已关闭")


# 全局单例
_store_manager: Optional[StoreManager] = None


def get_store_manager() -> StoreManager:
    """
    获取全局 Store 管理器实例（单例模式）

    Returns:
        StoreManager 实例
    """
    global _store_manager
    if _store_manager is None:
        # 默认使用 SQLite 持久化存储
        backend = "sqlite"
        _store_manager = StoreManager(store_backend=backend)
    return _store_manager
