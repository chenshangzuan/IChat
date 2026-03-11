"""
测试 Java Hello World 代码生成

验证 coder-agent 是否被正确委托
"""
import asyncio
import logging
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)

logger = logging.getLogger(__name__)


async def test_java_hello():
    """测试 Java Hello World 生成"""
    from demos.deepagents_demo import chat_response_with_metadata

    print("\n" + "=" * 60)
    print("🧪 测试: 用 Java 写一个 Hello World")
    print("=" * 60)

    result = await chat_response_with_metadata(
        user_input="用java 写一个hello world",
        session_id="test-java-hello"
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

        if summary.get('delegations'):
            print(f"\n🔄 委托详情:")
            for i, delegation in enumerate(summary['delegations'], 1):
                print(f"   [{i}] {delegation['from_agent']} → {delegation['to_agent']}")
                print(f"       工具: {delegation['tool_name']}")

    # 显示响应内容（前 500 字符）
    print(f"\n📝 响应内容预览:")
    print("-" * 60)
    content_preview = result['response'][:500]
    print(content_preview)
    if len(result['response']) > 500:
        print("...")
    print("-" * 60)

    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_java_hello())
