"""
简单测试 Agent 功能

快速验证：
1. 后端 API 正常响应
2. AgentTracker 日志输出
3. 元数据返回
"""
import asyncio
import json
import logging
import sys

# 设置日志 - 确保在终端中可见
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)

logger = logging.getLogger(__name__)


async def test():
    """简单测试"""
    from demos.deepagents_chat import chat_response

    print("\n" + "=" * 60)
    print("🧪 Agent 跟踪测试")
    print("=" * 60)

    result = await chat_response(
        user_input="1+1等于几？",
        session_id="test-simple"
    )

    print("\n✅ 响应成功!")
    print(f"   Agent 类型: {result['agent']}")
    print(f"   响应长度: {len(result['response'])} 字符")

    if result.get('tracker_summary'):
        summary = result['tracker_summary']
        print(f"\n📊 跟踪统计:")
        print(f"   - 委托次数: {summary.get('delegation_count', 0)}")
        print(f"   - 工具调用: {summary.get('tool_call_count', 0)}")
        print(f"   - 总耗时: {summary.get('duration', 0):.2f} 秒")

    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test())
