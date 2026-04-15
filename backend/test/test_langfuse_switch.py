"""测试Langfuse开关功能"""
import os
import sys
sys.path.insert(0, '.')

def test_switch_disabled():
    """测试开关关闭时"""
    print("\n=== 测试1: 开关关闭 (默认) ===")
    from common.langfuse import get_langfuse_handler
    handler = get_langfuse_handler()
    assert handler is None, "开关关闭时handler应为None"
    print("✅ 开关关闭: handler为None")

def test_config_values():
    """测试配置值"""
    print("\n=== 测试2: 配置值 ===")
    from common.config import config
    print(f"LANGFUSE_TRACING: {config.LANGFUSE_TRACING}")
    print(f"LANGFUSE_PUBLIC_KEY: {'已设置' if config.LANGFUSE_PUBLIC_KEY else '未设置'}")
    print(f"LANGFUSE_HOST: {config.LANGFUSE_HOST}")

def test_session_manager_callbacks():
    """测试session_manager中的callback配置"""
    print("\n=== 测试3: SessionManager Callback配置 ===")
    import asyncio
    from common.session_manager import get_session_manager

    async def test():
        manager = get_session_manager()
        config = await manager.get_config('test-session', 'deepagents')
        print(f"Config有callbacks: {'callbacks' in config}")
        if 'callbacks' in config:
            print(f"Callbacks数量: {len(config['callbacks'])}")
        else:
            print("无callbacks (因为LANGFUSE_TRACING=false)")
        return config

    config = asyncio.run(test())
    return config

if __name__ == "__main__":
    try:
        test_switch_disabled()
        test_config_values()
        config = test_session_manager_callbacks()
        print("\n✅ 所有测试通过!")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
