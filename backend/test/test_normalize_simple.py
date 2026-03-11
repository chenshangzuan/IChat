"""
简单测试审计日志规范化
"""
import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test():
    from demos.deepagents_demo import chat_response

    print("=" * 60)
    print("测试: create_ecs_instance 规范化")
    print("=" * 60)

    response = await chat_response(
        "将 create_ecs_instance 转换为标准接口行为描述，格式为 [Action] [Service] [Resource]",
        "test-simple"
    )

    print("\n" + "=" * 60)
    print("响应:")
    print("=" * 60)
    print(response)
    print("\n" + "=" * 60)
    print(f"包含 'Create ZEC Instance': {'Create ZEC Instance' in response}")
    print("=" * 60)

asyncio.run(test())
