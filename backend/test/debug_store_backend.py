"""
调试 StoreBackend 问题
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

async def test_store_backend():
    """测试 StoreBackend 是否正确工作"""
    from langchain.tools import ToolRuntime
    from deepagents.backends import StoreBackend, StateBackend, CompositeBackend
    from deepagents.backends.store import BackendContext
    from common.store_manager import get_store_manager

    # 获取 store
    store_manager = get_store_manager()
    store = await store_manager.get_store()
    print(f"✅ Store 类型: {type(store).__name__}")

    # 创建模拟 runtime
    class MockRuntime:
        def __init__(self, store):
            self.store = store
            self.state = {}
            self.config = {}

    runtime = MockRuntime(store)

    # 测试 StoreBackend
    def get_memories_namespace(ctx: BackendContext) -> tuple[str, ...]:
        return ("memories",)

    store_backend = StoreBackend(runtime, namespace=get_memories_namespace)
    print(f"✅ StoreBackend 创建成功")

    # 测试写入
    result = await store_backend.awrite("/memories/test.md", "# Test\nHello World")
    print(f"📝 写入结果: {result}")

    if result.error:
        print(f"❌ 写入错误: {result.error}")
    else:
        print(f"✅ 写入成功: {result.path}")

        # 测试读取
        content = await store_backend.aread("/memories/test.md")
        print(f"📖 读取内容:\n{content[:200]}")

    # 测试 ls
    infos = await store_backend.als_info("/memories/")
    print(f"📋 ls 结果: {[info['path'] for info in infos]}")

    # 检查数据库
    print("\n📊 数据库内容:")
    import sqlite3
    conn = sqlite3.connect("data/deepagent_demo.db")
    cursor = conn.execute("SELECT namespace, key FROM store WHERE namespace LIKE '%memories%'")
    for row in cursor.fetchall():
        print(f"  {row[0]}|{row[1]}")
    conn.close()

async def test_composite_backend():
    """测试 CompositeBackend 路由"""
    from langchain.tools import ToolRuntime
    from deepagents.backends import StoreBackend, StateBackend, CompositeBackend
    from deepagents.backends.store import BackendContext
    from common.store_manager import get_store_manager

    # 获取 store
    store_manager = get_store_manager()
    store = await store_manager.get_store()

    # 创建模拟 runtime
    class MockRuntime:
        def __init__(self, store):
            self.store = store
            self.state = {}
            self.config = {}

    runtime = MockRuntime(store)

    # 创建 CompositeBackend
    def get_memories_namespace(ctx: BackendContext) -> tuple[str, ...]:
        return ("memories",)

    def make_backend(runtime):
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={
                "/memories/": StoreBackend(runtime, namespace=get_memories_namespace)
            }
        )

    backend = make_backend(runtime)
    print(f"✅ CompositeBackend 创建成功")

    # 测试写入 /memories/ 路径
    result = await backend.awrite("/memories/preferences.md", "# Preferences\nLanguage: Python")
    print(f"📝 写入 /memories/preferences.md: {result}")

    # 测试写入普通路径
    result = await backend.awrite("/temp/test.txt", "Temporary content")
    print(f"📝 写入 /temp/test.txt: {result}")

    # 检查数据库
    print("\n📊 数据库内容:")
    import sqlite3
    conn = sqlite3.connect("data/deepagent_demo.db")
    cursor = conn.execute("SELECT namespace, key FROM store")
    for row in cursor.fetchall():
        print(f"  {row[0]}|{row[1]}")
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("测试 1: StoreBackend")
    print("=" * 60)
    asyncio.run(test_store_backend())

    print("\n" + "=" * 60)
    print("测试 2: CompositeBackend 路由")
    print("=" * 60)
    asyncio.run(test_composite_backend())
