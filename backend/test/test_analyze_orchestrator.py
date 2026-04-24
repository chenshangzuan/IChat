"""
分析 Orchestrator 行为

查看详细的消息历史，确认是否调用了 task 工具
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout,
)


async def analyze_orchestrator():
    """分析 Orchestrator 是否正确委托"""
    print("\n" + "=" * 60)
    print("🔍 分析: Orchestrator 委托行为")
    print("=" * 60)

    from demos.deepagents_chat import chat_response

    user_query = "帮我写一个java的冒泡排序"

    print(f"\n📝 用户问题: {user_query}")
    print("-" * 40)

    result = await chat_response(
        user_input=user_query,
        session_id="analyze-orchestrator"
    )

    print(f"\n📊 分析结果:")
    print("=" * 60)

    # 查看 tracker summary
    tracker_summary = result.get("tracker_summary", {})
    print(f"Agent 类型: {result.get('agent')}")
    print(f"工具调用数量: {tracker_summary.get('tool_call_count', 0)}")
    print(f"委托次数: {tracker_summary.get('delegation_count', 0)}")

    # 查看工具调用详情
    print(f"\n🔧 工具调用详情:")
    print("-" * 40)
    tool_calls = tracker_summary.get('tool_calls', [])
    for i, tc in enumerate(tool_calls):
        print(f"\n[{i}] 工具: {tc.get('tool_name')}")
        print(f"    参数: {tc.get('args')}")
        print(f"    执行者: {tc.get('agent_name')}")
        print(f"    状态: {tc.get('status')}")

    # 查看响应历史
    print(f"\n💬 响应历史:")
    print("-" * 40)
    responses = tracker_summary.get('responses', [])
    for i, resp in enumerate(responses):
        agent_type = resp.get('agent_type', 'unknown')
        content = resp.get('content', '')[:100]
        print(f"\n[{i}] Agent: {resp.get('agent_name')} ({agent_type})")
        print(f"    内容: {content}...")

    # 判断是否正确委托
    has_task_call = any(tc.get('tool_name') == 'task' for tc in tool_calls)
    has_coder_response = any(resp.get('agent_type') == 'coder' for resp in responses)

    print(f"\n✅ 验证结果:")
    print("-" * 40)
    print(f"  - 调用了 task 工具: {has_task_call}")
    print(f"  - 有 Coder Agent 响应: {has_coder_response}")

    if has_task_call and has_coder_response:
        print("\n✅ Orchestrator 正确委托给了 Coder Agent")
    elif not has_task_call:
        print("\n❌ Orchestrator 没有调用 task 工具，直接回答了问题")
        print("   原因: Orchestrator 可能认为这个问题不需要委托")
    else:
        print("\n⚠️ 调用了 task 工具但没有 Coder Agent 响应")

    print("\n" + "=" * 60)
    print("✅ 分析完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(analyze_orchestrator())
