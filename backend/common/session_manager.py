"""
会话管理器 - 统一管理所有会话状态

使用 LangGraph 的 Checkpointer 机制实现会话记忆：
- 默认使用 AsyncSqliteSaver（LangGraph 标准 SQLite 持久化存储）
"""
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver
import pathlib
import logging

from common.langfuse import get_langfuse_handler

logger = logging.getLogger(__name__)


class SessionManager:
    """会话管理器"""

    def __init__(self, checkpoint_backend: str = "sqlite"):
        """
        初始化会话管理器

        Args:
            checkpoint_backend: 存储后端类型 ("memory" 或 "sqlite"，默认 "sqlite")
        """
        self._checkpoint_backend = checkpoint_backend
        self.checkpointer = None  # 延迟初始化
        self._active_sessions: dict = {}
        logger.info(f"📝 [SessionManager] 初始化完成，后端: {checkpoint_backend}")

    async def _ensure_checkpointer(self):
        """确保 checkpointer 已初始化"""
        if self.checkpointer is None:
            self.checkpointer = await self._create_checkpointer(self._checkpoint_backend)
            logger.info(f"✅ [SessionManager] Checkpointer 已创建: {type(self.checkpointer).__name__}")
        return self.checkpointer

    def _create_checkpointer(self, backend: str):
        """
        创建 checkpointer 实例（同步版本，仅用于 memory）

        Args:
            backend: 存储后端类型

        Returns:
            Checkpointer 实例
        """
        if backend == "memory":
            return MemorySaver()
        else:
            # SQLite 需要异步初始化，使用 _ensure_checkpointer
            raise ValueError(f"Backend '{backend}' requires async initialization")

    async def _create_checkpointer(self, backend: str):
        """
        异步创建 checkpointer 实例

        Args:
            backend: 存储后端类型

        Returns:
            Checkpointer 实例
        """
        if backend == "memory":
            return MemorySaver()
        elif backend == "sqlite":
            import aiosqlite
            from common.checkpoint.json_sqlite_saver import DebugAsyncSqliteSaver
            db_path = pathlib.Path("data/deepagent_demo.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = await aiosqlite.connect(str(db_path))
            return DebugAsyncSqliteSaver(conn)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def get_config(self, session_id: str, demo_id: str) -> dict:
        """
        获取会话配置（用于 LangGraph invoke/config）

        Args:
            session_id: 会话 ID
            demo_id: Demo ID

        Returns:
            LangGraph 配置字典，包含 thread_id
        """
        thread_id = f"{demo_id}:{session_id}"
        # 构建基础配置
        config_dict = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 100,
        }

        # Langfuse追踪
        handler = get_langfuse_handler()
        if handler:
            config_dict["callbacks"] = [handler]  # callbacks必须是列表
            logger.debug(f"🔑 [SessionManager] Langfuse callback 已添加")
        return config_dict

    async def get_config(self, session_id: str, demo_id: str) -> dict:
        """
        获取会话配置（用于 LangGraph invoke/config）

        Args:
            session_id: 会话 ID
            demo_id: Demo ID

        Returns:
            LangGraph 配置字典，包含 thread_id 和 callbacks
        """
        # 确保 checkpointer 已初始化
        await self._ensure_checkpointer()
        thread_id = f"{demo_id}:{session_id}"

        # 构建基础配置
        config_dict = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 100  # 每次工具调用占 2 步，skill 工作流（读文件+执行）需要更多步数
        }

        # Langfuse追踪
        handler = get_langfuse_handler()
        if handler:
            config_dict["callbacks"] = [handler]  # callbacks必须是列表
            logger.debug(f"🔑 [SessionManager] Langfuse callback 已添加")
        return config_dict

    async def clear_session(self, session_id: str, demo_id: str):
        """
        清理指定会话的 checkpoint

        Args:
            session_id: 会话 ID
            demo_id: Demo ID
        """
        await self._ensure_checkpointer()
        thread_id = f"{demo_id}:{session_id}"

        # 直接通过 SQL 删除 checkpoint 和 writes 记录
        async with self.checkpointer.lock:
            await self.checkpointer.conn.execute(
                "DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,)
            )
            await self.checkpointer.conn.execute(
                "DELETE FROM writes WHERE thread_id = ?", (thread_id,)
            )
            await self.checkpointer.conn.commit()

        # 从活跃会话中移除
        session_key = f"{demo_id}:{session_id}"
        self._active_sessions.pop(session_key, None)

        logger.info(f"🗑️ [SessionManager] 清理会话: {thread_id}")


# 全局单例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    获取全局会话管理器实例（单例模式）

    Returns:
        SessionManager 实例
    """
    global _session_manager
    if _session_manager is None:
        from common.config import config
        # 默认使用 SQLite 持久化存储
        backend = "sqlite"
        _session_manager = SessionManager(checkpoint_backend=backend)
    return _session_manager
