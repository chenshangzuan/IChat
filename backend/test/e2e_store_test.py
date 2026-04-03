"""
端到端测试：验证 Agent 运行时 StoreBackend 是否正常工作
"""
import asyncio
import logging
import sys
import sqlite3

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)

async def test_agent_with_store():
    """测试 Agent 调用时 Store 是否正常工作"""
    from agents import get_orchestrator_with_store
    from common.session_manager import get_session_manager

    # 获取 orchestrator
    print("=" * 60)
    print("🚀 创建 Orchestrator...")
    orchestrator = await get_orchestrator_with_store()
    print(f"✅ Orchestrator 创建成功")

    # 获取会话配置
    session_manager = get_session_manager()
    config = await session_manager.get_config("test-store", "deepagents")
    print(f"📝 Config: {config}")

    # 发送测试消息
    print("\n" + "=" * 60)
    print("📤 发送测试消息...")

    try:
        result = await orchestrator.ainvoke(
            {"messages": [{"role": "user", "content": "请使用 write_file 工具在 /memories/preferences.md 路径写入我的开发语言偏好：我喜欢使用 Python 和 TypeScript"}]},
            config=config
        )

        print("\n" + "=" * 60)
        print("📥 响应结果:")

        for i, msg in enumerate(result["messages"]):
            msg_type = getattr(msg, 'type', 'unknown')
            msg_class = type(msg).__name__
            content = msg.content if hasattr(msg, 'content') else str(msg)

            # 检查是否有工具调用
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    if isinstance(tc, dict):
                        tool_name = tc.get('name', 'unknown')
                        tool_args = tc.get('args', {})
                    else:
                        tool_name = getattr(tc, 'name', 'unknown')
                        tool_args = getattr(tc, 'args', {})
                    print(f"  [{i}] {msg_class} → 工具调用: {tool_name}({tool_args})")
            else:
                print(f"  [{i}] {msg_class}: {content[:200]}...")

        # 检查数据库
        print("\n" + "=" * 60)
        print("📊 检查数据库内容:")
        conn = sqlite3.connect("data/deepagent_demo.db")
        cursor = conn.execute("SELECT prefix, key FROM store")
        for row in cursor.fetchall():
            print(f"  {row[0]}|{row[1]}")
        conn.close()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_with_store())
