"""
Demo 1: 基础 LLM 问答
最简单的对话功能，用于验证前后端联通
"""
from typing import AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from models import default_llm


# 对话历史存储（简单的内存存储）
class ChatHistory:
    def __init__(self):
        self.messages: list[tuple[str, str]] = []

    def add_message(self, user_input: str, ai_response: str):
        """添加对话记录"""
        self.messages.append((user_input, ai_response))

    def get_history(self, limit: int = 10) -> list[BaseMessage]:
        """获取对话历史（转换为 LangChain 消息格式）"""
        history = []
        for user_msg, ai_msg in self.messages[-limit:]:
            history.append(HumanMessage(content=user_msg))
            history.append(AIMessage(content=ai_msg))
        return history

    def clear(self):
        """清空历史"""
        self.messages.clear()


# 全局对话历史存储（按 session_id 分隔）
_session_histories: dict[str, ChatHistory] = {}


def _get_history(session_id: str) -> ChatHistory:
    """获取指定会话的历史记录"""
    if session_id not in _session_histories:
        _session_histories[session_id] = ChatHistory()
    return _session_histories[session_id]


async def chat_response(user_input: str, session_id: str = "default") -> str:
    """
    生成聊天响应

    Args:
        user_input: 用户输入
        session_id: 会话 ID（用于区分不同会话）

    Returns:
        AI 响应
    """
    # 获取指定会话的对话历史
    history = _get_history(session_id).get_history()

    # 构建消息列表（历史 + 当前输入）
    messages = history + [HumanMessage(content=user_input)]

    # 直接调用模型
    response = await default_llm.ainvoke(messages)

    # 保存到该会话的历史
    _get_history(session_id).add_message(user_input, response.content)

    return response.content


async def chat_stream(user_input: str, session_id: str = "default") -> AsyncIterator[str]:
    """
    流式聊天响应

    Args:
        user_input: 用户输入
        session_id: 会话 ID

    Yields:
        AI 响应的片段
    """
    # 获取指定会话的对话历史
    history = _get_history(session_id).get_history()

    # 构建消息列表（历史 + 当前输入）
    messages = history + [HumanMessage(content=user_input)]

    # 流式调用
    async for chunk in default_llm.astream(messages):
        if hasattr(chunk, 'content'):
            yield chunk.content
        else:
            yield str(chunk)

    # 保存完整响应到历史（这里简化处理）
    # 实际应用中需要收集完整响应后再保存


def clear_history(session_id: str = "default"):
    """清空对话历史"""
    if session_id in _session_histories:
        _session_histories[session_id].clear()
