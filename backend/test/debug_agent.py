"""
调试 agent 检测逻辑
"""
import asyncio


async def debug_test():
    """调试测试"""
    from demos.deepagents_demo import chat_response_with_metadata
    from demos.deepagents_demo import detect_agent

    result = await chat_response_with_metadata(
        user_input="用java写一个hello world",
        session_id="debug-test"
    )

    print("\n" + "=" * 60)
    print("📋 调试信息:")
    print("=" * 60)

    # 检查最终响应
    final_response = result["response"]
    print(f"\n最终响应: {final_response}")
    print(f"检测到的 agent: {result['agent']}")

    # 手动测试检测逻辑
    detected = detect_agent(final_response)
    print(f"手动检测结果: {detected}")

    # 检查消息历史
    print("\n" + "=" * 60)
    print("📋 消息历史:")
    print("=" * 60)
    for i, msg in enumerate(result["all_messages"]):
        msg_type = getattr(msg, 'type', 'unknown')
        content = msg.content if hasattr(msg, 'content') else ""
        short_content = content[:80] if len(content) > 80 else content
        print(f"\n[{i}] {msg_type}: {short_content}")

        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    print(f"    🔧 工具: {tc.get('name')}")
                    args = tc.get('args', {})
                    if 'subagent_type' in args:
                        print(f"       → 子代理: {args['subagent_type']}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(debug_test())
