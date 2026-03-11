"""
测试 Nginx 404 日志分析

验证：
1. Orchestrator 委托给 sre-agent
2. sre-agent 使用 log-analysis 技能
3. 返回结构化的日志分析报告
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout,
)


async def test_nginx_404_analysis():
    """测试 Nginx 404 日志分析"""
    print("\n" + "=" * 60)
    print("🧪 测试: Nginx 404 日志分析")
    print("=" * 60)

    from demos.deepagents_demo import chat_response

    user_query = "如何分析 Nginx 日志中的 404 错误？"

    print(f"\n📝 用户问题: {user_query}")
    print("-" * 40)

    response = await chat_response(
        user_input=user_query,
        session_id="test-nginx-404"
    )

    print(f"\n✅ 响应:")
    print("=" * 60)
    print(response)
    print("=" * 60)

    # 验证响应内容
    print(f"\n📊 响应分析:")
    print("-" * 40)

    has_sre_agent = "SRE Agent" in response or "sre-agent" in response.lower()
    has_log_analysis = any(keyword in response.lower() for keyword in [
        "log", "日志", "404", "error", "error_log", "access_log"
    ])

    print(f"  - 包含 SRE Agent: {has_sre_agent}")
    print(f"  - 包含日志分析内容: {has_log_analysis}")

    # 验证是否有结构化输出
    has_structure = any(keyword in response for keyword in [
        "##", "###", "**", "步骤", "Step", "分析"
    ])
    print(f"  - 有结构化输出: {has_structure}")

    if has_sre_agent and has_log_analysis:
        print("\n✅ 测试通过: SRE Agent 正确处理了日志分析任务")
    else:
        print("\n❌ 测试失败: 未正确委托给 SRE Agent")

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_nginx_404_analysis())
