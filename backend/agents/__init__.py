"""
Agent 模块

包含 Deep Agents Multi-Agent 系统的配置和初始化。
"""
from .deepagents import orchestrator, create_orchestrator, create_orchestrator_with_store

__all__ = [
    "orchestrator",
    "create_orchestrator",
    "create_orchestrator_with_store",
    "get_orchestrator_with_checkpointer",
    "get_orchestrator_with_store",
]


async def get_orchestrator_with_checkpointer():
    """
    获取带 checkpointer 的 orchestrator（异步版本）

    使用会话管理器的 checkpointer，支持多轮对话记忆。
    会自动等待 checkpointer 异步初始化完成。

    Returns:
        配置了 checkpointer 的 orchestrator agent
    """
    from common.session_manager import get_session_manager
    session_manager = get_session_manager()
    # 确保 checkpointer 已初始化
    await session_manager._ensure_checkpointer()
    return create_orchestrator(checkpointer=session_manager.checkpointer)


async def get_orchestrator_with_store():
    """
    获取带 checkpointer 和 store 的 orchestrator（异步版本）

    支持多轮对话记忆和跨线程长期记忆。

    Returns:
        配置了 checkpointer 和 store 的 orchestrator agent
    """
    from common.session_manager import get_session_manager
    from common.store_manager import get_store_manager

    session_manager = get_session_manager()
    await session_manager._ensure_checkpointer()

    store_manager = get_store_manager()
    store = await store_manager.get_store()

    return create_orchestrator(
        checkpointer=session_manager.checkpointer,
        store=store
    )
