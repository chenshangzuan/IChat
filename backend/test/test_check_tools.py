import asyncio
from demos.deepagents_chat import chat_response

async def test():
    result = await chat_response("帮我写一个java的冒泡排序", "test-check")
    response = result["response"]

    print(f"响应长度: {len(response)}")
    print(f"包含代码: {'```' in response}")
    print(f"Agent: {result['agent']}")

    tracker = result["tracker_summary"]
    print(f"工具调用数: {tracker['tool_call_count']}")
    print(f"委托次数: {tracker['delegation_count']}")

    # 检查是否有 task 工具调用
    tool_calls = tracker.get('tool_calls', [])
    print(f"工具调用详情:")
    for tc in tool_calls:
        print(f"  - {tc.get('tool_name')}: {tc.get('agent_name')}")

    if len(response) > 1000:
        print(f"\n✅ 有完整代码!")
        print(f"代码预览:\n{response[:500]}...")
    else:
        print(f"\n⚠️ 只有摘要:")
        print(response)

asyncio.run(test())
