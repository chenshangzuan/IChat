"""
Skill 追踪中间件 - 上下文变量管理

使用 context vars 存储 skill 调用信息，避免通过中间件传递状态。
"""
from contextvars import ContextVar
from typing import Dict, Any, List

# 创建上下文变量，存储 skill 调用列表
_skill_calls_context: ContextVar[List[Dict[str, Any]]] = ContextVar('skill_calls_context', default=[])


def get_skill_calls_context() -> List[Dict[str, Any]]:
    """获取当前上下文中的 skill 调用列表"""
    return _skill_calls_context.get()


def set_skill_calls_context(calls: List[Dict[str, Any]]):
    """设置当前上下文中的 skill 调用列表"""
    _skill_calls_context.set(calls)


def add_skill_call(skill_call: Dict[str, Any]):
    """
    添加一个 skill 调用记录到上下文

    Args:
        skill_call: 包含 skill_name, agent_name, agent_type, task_summary 等信息的字典
    """
    current_calls = get_skill_calls_context()
    updated_calls = current_calls + [skill_call]
    _skill_calls_context.set(updated_calls)


def clear_skill_calls_context():
    """清空当前上下文中的 skill 调用列表"""
    _skill_calls_context.set([])
