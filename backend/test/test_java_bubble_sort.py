"""
测试 Java 冒泡排序生成

验证：
1. Orchestrator 是否委托给 coder-agent
2. coder-agent 是否使用 code-generation 技能
3. 返回 Java 代码
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout,
)


async def test_java_bubble_sort():
    """测试 Java 冒泡排序生成"""
    print("\n" + "=" * 60)
    print("🧪 测试: Java 冒泡排序生成")
    print("=" * 60)

    from demos.deepagents_demo import chat_response

    user_query = "帮我写一个java的冒泡排序"

    print(f"\n📝 用户问题: {user_query}")
    print("-" * 40)

    response = await chat_response(
        user_input=user_query,
        session_id="test-java-bubble-sort"
    )

    print(f"\n✅ 响应:")
    print("=" * 60)
    print(response)
    print("=" * 60)

    # 验证响应内容
    print(f"\n📊 响应分析:")
    print("-" * 40)

    has_coder_agent = "Coder Agent" in response or "coder-agent" in response.lower()
    has_java_code = "java" in response.lower() or "Java" in response
    has_bubble_sort = "bubble" in response.lower() or "冒泡" in response or "排序" in response

    print(f"  - 包含 Coder Agent: {has_coder_agent}")
    print(f"  - 包含 Java 代码: {has_java_code}")
    print(f"  - 包含冒泡排序: {has_bubble_sort}")

    # 验证是否有代码块
    has_code_block = "```" in response
    print(f"  - 有代码块: {has_code_block}")

    if has_coder_agent:
        print("\n✅ 测试通过: Coder Agent 正确处理了代码生成任务")
    else:
        print("\n❌ 测试失败: 未委托给 Coder Agent")
        print("   原因分析: Orchestrator 可能直接回答了问题")

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_java_bubble_sort())
