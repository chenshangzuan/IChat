"""
Agent 模块

包含 Deep Agents Multi-Agent 系统的配置和初始化。
"""
from .deepagents import orchestrator, create_orchestrator
from .skill_tracking_middleware import (
    get_skill_calls_context,
    set_skill_calls_context,
    add_skill_call,
    clear_skill_calls_context,
)

__all__ = [
    "orchestrator",
    "create_orchestrator",
    "get_orchestrator_with_checkpointer",
    "get_skill_calls_context",
    "set_skill_calls_context",
    "add_skill_call",
    "clear_skill_calls_context",
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
