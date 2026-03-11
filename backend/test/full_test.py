"""
查看完整的消息历史，包括 sre-agent 的响应
"""
import asyncio


async def full_test():
    """完整测试"""
    from agents.deepagents import orchestrator

    print("测试: Nginx 502 错误分析")
    print("=" * 60)

    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": "Nginx 502 错误怎么解决？简短回答"}]
    })

    print("\n" + "=" * 60)
    print("📋 完整消息历史:")
    print("=" * 60)

    for i, msg in enumerate(result["messages"]):
        msg_type = getattr(msg, 'type', 'unknown')
        content = msg.content if hasattr(msg, 'content') else ""

        # 只显示前 100 字符
        short_content = content[:100] if len(content) > 100 else content

        print(f"\n[{i}] 类型: {msg_type}")
        print(f"    内容: {short_content}...")

        # 检查工具调用
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    print(f"    🔧 工具: {tc.get('name')}")
                    args = tc.get('args', {})
                    if 'subagent_type' in args:
                        print(f"       → 子代理: {args['subagent_type']}")
                else:
                    print(f"    🔧 工具: {tc.name}")

    print("\n" + "=" * 60)
    print("📋 最终响应:")
    print("=" * 60)
    final_msg = result["messages"][-1]
    print(final_msg.content)
    print("=" * 60)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(full_test())
