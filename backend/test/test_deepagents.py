"""
测试 DeepAgents Multi-Agent 系统

用于验证 agent 调用链和响应格式
"""
import asyncio
import logging
from demos.deepagents_demo import chat_response

logging.basicConfig(level=logging.INFO)


async def test_coder_task():
    """测试代码任务 - 应该委托给 coder-agent"""
    print("\n" + "=" * 60)
    print("🧪 测试 1: 代码任务 (应该委托给 Coder Agent)")
    print("=" * 60)

    response = await chat_response(
        user_input="请帮我写一个快速排序算法",
        session_id="test-001"
    )

    print("\n📝 响应内容:")
    print("-" * 60)
    print(response[:500])  # 只打印前 500 字符
    print("-" * 60)

    # 检查响应中是否包含 agent 标识
    if "👨‍💻 **Coder Agent**:" in response:
        print("\n✅ 检测到 Coder Agent 响应!")
    elif "🎯 **Delegating to" in response:
        print("\n✅ 检测到 Orchestrator 委托!")
    else:
        print("\n⚠️  未检测到明确的 agent 标识")


async def test_sre_task():
    """测试运维任务 - 应该委托给 sre-agent"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 运维任务 (应该委托给 SRE Agent)")
    print("=" * 60)

    response = await chat_response(
        user_input="如何分析 Nginx 日志中的 502 错误？",
        session_id="test-002"
    )

    print("\n📝 响应内容:")
    print("-" * 60)
    print(response[:500])  # 只打印前 500 字符
    print("-" * 60)

    # 检查响应中是否包含 agent 标识
    if "🔧 **SRE Agent**:" in response:
        print("\n✅ 检测到 SRE Agent 响应!")
    elif "🎯 **Delegating to" in response:
        print("\n✅ 检测到 Orchestrator 委托!")
    else:
        print("\n⚠️  未检测到明确的 agent 标识")


async def main():
    """运行所有测试"""
    await test_coder_task()
    await test_sre_task()

    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
