"""
测试 Agent 跟踪和日志功能

验证：
1. AgentTracker 的日志输出
2. 工具调用监控
3. 委托事件记录
4. 元数据返回
"""
import asyncio
import logging
from demos.deepagents_demo import chat_response_with_metadata

logging.basicConfig(level=logging.INFO)


async def test_agent_tracking():
    """测试 agent 跟踪功能"""
    print("\n" + "=" * 80)
    print("🧪 测试: Agent 跟踪和日志功能")
    print("=" * 80)

    result = await chat_response_with_metadata(
        user_input="请帮我写一个快速排序算法",
        session_id="test-tracking-001"
    )

    print("\n" + "=" * 80)
    print("📊 结果摘要")
    print("=" * 80)
    print(f"✅ 响应长度: {len(result['response'])} 字符")
    print(f"🤖 检测到的 Agent: {result['agent']}")

    if result.get('tracker_summary'):
        summary = result['tracker_summary']
        print(f"\n📈 跟踪统计:")
        print(f"  - 委托次数: {summary.get('delegation_count', 0)}")
        print(f"  - 工具调用: {summary.get('tool_call_count', 0)}")
        print(f"  - 响应数量: {summary.get('response_count', 0)}")
        print(f"  - 总耗时: {summary.get('duration', 0):.2f} 秒")

        if summary.get('delegations'):
            print(f"\n🔄 委托事件:")
            for i, delegation in enumerate(summary['delegations'], 1):
                print(f"  [{i}] {delegation['from_agent']} → {delegation['to_agent']}")
                print(f"      工具: {delegation['tool_name']}")
                print(f"      任务: {delegation['task_description'][:80]}...")

        if summary.get('tool_calls'):
            print(f"\n⚙️  工具调用:")
            for i, tc in enumerate(summary['tool_calls'], 1):
                print(f"  [{i}] {tc['tool_name']} (状态: {tc['status']})")
                print(f"      执行者: {tc['agent_name']}")

    print("\n" + "=" * 80)
    print("🎉 测试完成!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_agent_tracking())
