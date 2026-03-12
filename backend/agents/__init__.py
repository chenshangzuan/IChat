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
    "get_skill_calls_context",
    "set_skill_calls_context",
    "add_skill_call",
    "clear_skill_calls_context",
]
