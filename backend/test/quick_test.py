"""
快速测试 SRE 任务 - 只检查是否调用了 task 工具
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stdout,
)


async def quick_test():
    """快速测试"""
    from demos.deepagents_demo import chat_response

    # 简单的 SRE 任务
    response = await chat_response(
        user_input="Nginx 出现 502 错误怎么办？",
        session_id="quick-test"
    )

    print("\n" + "=" * 60)
    print("📋 响应内容:")
    print("=" * 60)
    print(response[:300])
    print("=" * 60)

    # 检查是否包含 SRE agent 标识
    if "sre" in response.lower():
        print("✅ 检测到 SRE Agent")
    else:
        print("❌ 未检测到 SRE Agent")

    if "🔧" in response:
        print("✅ 包含 agent 图标")
    else:
        print("❌ 不包含 agent 图标")


if __name__ == "__main__":
    asyncio.run(quick_test())
