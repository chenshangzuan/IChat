"""SSE (Server-Sent Events) 格式化工具函数

SSE 规范要求多行 data 必须拆成多个 data: 行，否则内容中的 \\n 会产生假的事件边界。
"""


def _encode_data(text: str) -> str:
    """将可能含换行的文本编码为 SSE 多行 data: 格式"""
    return "\n".join(f"data: {line}" for line in text.split("\n"))


def sse_content(text: str) -> str:
    """格式化普通文本 token 为 SSE data 帧"""
    return f"{_encode_data(text)}\n\n"


def sse_event(event_type: str, data: str) -> str:
    """格式化命名事件为 SSE 帧（tool_call / approval / metadata / error）"""
    return f"event: {event_type}\n{_encode_data(data)}\n\n"
