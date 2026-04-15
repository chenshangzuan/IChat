"""测试callbacks修复"""
import asyncio
import sys
sys.path.insert(0, '.')

async def main():
    from common.session_manager import get_session_manager
    from common.langfuse import get_langfuse_handler

    print("=== 测试Callbacks修复 ===\n")

    # 测试1: 检查handler
    print("1. 检查Langfuse handler:")
    handler = get_langfuse_handler()
    print(f"   Handler: {handler}")
    print(f"   Handler类型: {type(handler)}")

    # 测试2: 获取config
    print("\n2. 获取SessionManager config:")
    manager = get_session_manager()
    config = await manager.get_config('test-session', 'deepagents')

    print(f"   Config键: {list(config.keys())}")
    print(f"   有callbacks: {'callbacks' in config}")

    if 'callbacks' in config:
        callbacks = config['callbacks']
        print(f"   Callbacks类型: {type(callbacks)}")
        print(f"   是列表: {isinstance(callbacks, list)}")
        if isinstance(callbacks, list) and len(callbacks) > 0:
            print(f"   第一个callback类型: {type(callbacks[0])}")

    print("\n✅ 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())
