"""测试流式输出的消息结构"""
import asyncio
import sys
sys.path.insert(0, '.')

from demos.deepagents_demo import chat_stream_with_metadata

async def main():
    print("=== 开始测试 ===")
    try:
        count = 0
        async for chunk in chat_stream_with_metadata('你好', 'test-debug'):
            count += 1
            print(f"[{count}] Chunk: {repr(chunk[:100])}")
            if count >= 5:
                break
        print(f"\n总共收到 {count} chunks")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
