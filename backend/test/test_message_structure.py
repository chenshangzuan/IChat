"""测试消息结构"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from agents.deepagents import create_orchestrator
    from common.session_manager import get_session_manager

    print("创建orchestrator...")
    orchestrator = create_orchestrator()
    session_manager = get_session_manager()
    config = await session_manager.get_config('test-msg-struct', 'deepagents')

    print("开始astream...")
    count = 0
    async for chunk in orchestrator.astream(
        {'messages': [{'role': 'user', 'content': '你好'}]},
        config=config,
        stream_mode="messages"
    ):
        count += 1
        print(f"\n=== Chunk {count} ===")
        print(f"类型: {type(chunk)}")
        print(f"类型名: {type(chunk).__name__}")

        # 打印所有属性
        if hasattr(chunk, '__dict__'):
            print(f"属性: {list(chunk.__dict__.keys())}")
        else:
            print(f"dir(): {[a for a in dir(chunk) if not a.startswith('_')][:10]}")

        # 检查是否有content
        if hasattr(chunk, 'content'):
            content = chunk.content
            print(f"有content: 类型={type(content).__name__}")
            if isinstance(content, str):
                print(f"内容长度: {len(content)}")
                if content:
                    print(f"内容预览: {repr(content[:100])}")
            else:
                print(f"内容(非字符串): {str(content)[:100]}")
        else:
            print("没有content属性")

        if count >= 3:
            break

    print(f"\n总共 {count} chunks")

if __name__ == "__main__":
    asyncio.run(test())
