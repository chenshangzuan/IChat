"""
直接测试 Orchestrator 是否会调用 task 工具
"""
import asyncio


async def direct_test():
    """直接测试"""
    from agents.deepagents import orchestrator

    print("测试: 分析 Nginx 日志中的 502 错误")
    print("=" * 60)

    # 只运行一次，看第一次响应
    result = await orchestrator.ainvoke({
        "messages": [{"role": "user", "content": "Nginx 出现 502 错误怎么办？"}]
    })

    # 检查最后一条消息
    last_msg = result["messages"][-1]
    print(f"最后消息类型: {last_msg.type}")
    print(f"最后消息内容: {last_msg.content[:200]}...")

    # 检查是否有工具调用
    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
        print(f"工具调用: {last_msg.tool_calls}")
    else:
        print("没有工具调用")

    # 检查消息历史中的 task 工具调用
    print("\n消息历史中的工具调用:")
    for i, msg in enumerate(result["messages"]):
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.get('name') if isinstance(tc, dict) else tc.name
                print(f"  [{i}] 工具: {tool_name}")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(direct_test())
