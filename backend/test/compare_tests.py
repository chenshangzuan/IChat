"""
比较两个不同的测试结果

1. "用java写一个hello world" - 这次没有委托
2. "请帮我写一个快速排序算法" - 之前有委托
"""
import asyncio


async def compare():
    """比较测试"""
    from demos.deepagents_demo import chat_response_with_metadata

    # 测试 1: Java Hello World
    print("=" * 60)
    print("测试 1: 用java写一个hello world")
    print("=" * 60)

    result1 = await chat_response_with_metadata(
        user_input="用java写一个hello world",
        session_id="compare-1"
    )

    print(f"Agent 类型: {result1['agent']}")
    print(f"委托次数: {result1['tracker_summary']['delegation_count']}")

    # 检查消息历史中的 task 工具调用
    print("\n工具调用:")
    for i, msg in enumerate(result1['all_messages']):
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    tool_name = tc.get('name')
                    args = tc.get('args', {})
                    print(f"  [{i}] 工具: {tool_name}")
                    if 'subagent_type' in args:
                        print(f"      → 委托给: {args['subagent_type']}")

    # 测试 2: 快速排序（使用不同提示）
    print("\n" + "=" * 60)
    print("测试 2: 请帮我写一个快速排序算法（要求详细）")
    print("=" * 60)

    result2 = await chat_response_with_metadata(
        user_input="请帮我写一个快速排序算法，包含详细注释和测试用例",
        session_id="compare-2"
    )

    print(f"Agent 类型: {result2['agent']}")
    print(f"委托次数: {result2['tracker_summary']['delegation_count']}")

    # 检查消息历史中的 task 工具调用
    print("\n工具调用:")
    for i, msg in enumerate(result2['all_messages']):
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    tool_name = tc.get('name')
                    args = tc.get('args', {})
                    print(f"  [{i}] 工具: {tool_name}")
                    if 'subagent_type' in args:
                        print(f"      → 委托给: {args['subagent_type']}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(compare())
