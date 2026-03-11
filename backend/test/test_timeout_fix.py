"""
测试超时修复

验证：
1. 长时间任务不会超时
2. 错误被正确处理
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)


async def test():
    """测试修复效果"""
    from demos.deepagents_demo import chat_response_with_metadata

    print("\n" + "=" * 60)
    print("🧪 测试: 复杂任务（快速排序）")
    print("=" * 60)

    try:
        result = await chat_response_with_metadata(
            user_input="请帮我写一个快速排序算法",
            session_id="test-timeout"
        )

        print("\n✅ 请求成功!")
        print(f"   Agent 类型: {result['agent']}")
        print(f"   响应长度: {len(result['response'])} 字符")

        if result.get('tracker_summary'):
            summary = result['tracker_summary']
            print(f"\n📊 跟踪统计:")
            print(f"   - 委托次数: {summary.get('delegation_count', 0)}")
            print(f"   - 工具调用: {summary.get('tool_call_count', 0)}")
            print(f"   - 总耗时: {summary.get('duration', 0):.2f} 秒")

    except Exception as e:
        print(f"\n❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test())
