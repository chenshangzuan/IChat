"""
测试 skills 配置

验证：
1. skills 目录是否被正确识别
2. 子代理是否能使用 skills
3. 技能扩展是否正常工作
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout,
)


async def test_skills():
    """测试 skills 配置"""
    print("\n" + "=" * 60)
    print("🧪 测试: Skills 配置")
    print("=" * 60)

    from demos.deepagents_demo import chat_response

    # 测试代码生成技能
    print("\n测试 1: 代码生成 (应该使用 code-generation skill)")
    print("-" * 40)

    response1 = await chat_response(
        user_input="请用 Python 写一个二分查找算法",
        session_id="test-skills-1"
    )

    print(f"响应长度: {len(response1)} 字符")
    print(f"响应预览: {response1[:200]}...")

    # 测试 SRE 日志分析技能
    print("\n测试 2: 日志分析 (应该使用 log-analysis skill)")
    print("-" * 40)

    response2 = await chat_response(
        user_input="如何分析应用日志中的错误？",
        session_id="test-skills-2"
    )

    print(f"响应长度: {len(response2)} 字符")
    print(f"响应预览: {response2[:200]}...")

    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_skills())
