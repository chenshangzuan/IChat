"""测试SSE事件发送"""
import asyncio
import sys
sys.path.insert(0, '.')

from demos.deepagents_chat import chat_stream_with_metadata

async def main():
    print("=== 测试SSE事件类型 ===\n")

    event_stats = {
        'message': 0,
        'tool_call': 0,
        'approval': 0,
        'metadata': 0
    }

    count = 0
    async for chunk in chat_stream_with_metadata('写一首关于春天的诗到/memories/spring.txt', 'test-sse-events'):
        count += 1

        # 统计事件类型
        if chunk.startswith('data: '):
            event_stats['message'] += 1
        elif chunk.startswith('event: tool_call'):
            event_stats['tool_call'] += 1
            print(f"\n🔧 [工具调用 {event_stats['tool_call']}]")
            print(f"{chunk[:200]}...")
        elif chunk.startswith('event: approval'):
            event_stats['approval'] += 1
            print(f"\n📋 [审批事件 {event_stats['approval']}]")
            print(f"{chunk[:300]}...")
        elif chunk.startswith('event: metadata'):
            event_stats['metadata'] += 1
            print(f"\n📊 [元数据事件]")

        if count % 50 == 0:
            print(f'  进度: {count} chunks...')

    print(f"\n\n=== 统计结果 ===")
    print(f"总计chunks: {count}")
    print(f"消息事件: {event_stats['message']}")
    print(f"工具调用事件: {event_stats['tool_call']}")
    print(f"审批事件: {event_stats['approval']}")
    print(f"元数据事件: {event_stats['metadata']}")

if __name__ == "__main__":
    asyncio.run(main())
