"""
查看完整的响应内容

找出为什么显示 Unknown Agent
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    stream=sys.stdout,
)


async def check_response():
    """检查响应内容"""
    from demos.deepagents_demo import chat_response_with_metadata

    result = await chat_response_with_metadata(
        user_input="用java写一个hello world",
        session_id="check-response"
    )

    print("\n" + "=" * 60)
    print("📋 检测结果:")
    print("=" * 60)
    print(f"Agent 类型: {result['agent']}")
    print("=" * 60)

    print("\n" + "=" * 60)
    print("📋 完整响应内容:")
    print("=" * 60)
    print(repr(result['response']))
    print("=" * 60)

    print("\n" + "=" * 60)
    print("📋 消息历史:")
    print("=" * 60)
    for i, msg in enumerate(result.get('all_messages', [])):
        msg_type = getattr(msg, 'type', 'unknown')
        content = msg.content if hasattr(msg, 'content') else str(msg)
        print(f"[{i}] {msg_type}: {content[:100]}...")
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"    Tool calls: {msg.tool_calls}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_response())
