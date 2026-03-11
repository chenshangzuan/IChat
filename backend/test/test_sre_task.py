"""
测试 SRE 任务

检查为什么没有委托给 sre-agent
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.WARNING,  # 减少日志
    stream=sys.stdout,
)


async def test_sre():
    """测试 SRE 任务"""
    from demos.deepagents_demo import chat_response_with_metadata

    result = await chat_response_with_metadata(
        user_input="如何分析 Nginx 日志中的 502 错误？",
        session_id="test-sre"
    )

    print("\n" + "=" * 60)
    print("📋 测试结果:")
    print("=" * 60)
    print(f"Agent 类型: {result['agent']}")
    print(f"响应长度: {len(result['response'])} 字符")

    if result.get('tracker_summary'):
        summary = result['tracker_summary']
        print(f"\n📊 统计:")
        print(f"   - 委托次数: {summary.get('delegation_count', 0)}")
        print(f"   - 工具调用: {summary.get('tool_call_count', 0)}")

    print("\n" + "=" * 60)
    print("📋 完整响应:")
    print("=" * 60)
    print(result['response'][:500])
    print("=" * 60)

    # 检查消息历史
    print("\n" + "=" * 60)
    print("📋 消息历史:")
    print("=" * 60)
    for i, msg in enumerate(result.get('all_messages', [])[:5]):  # 只看前 5 条
        msg_type = getattr(msg, 'type', 'unknown')
        content = msg.content if hasattr(msg, 'content') else str(msg)[:100]
        print(f"[{i}] {msg_type}: {content}")
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"    🔧 工具调用: {msg.tool_calls}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sre())
