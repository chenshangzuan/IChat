"""
只监控前几轮的工具调用
"""
import asyncio


async def monitor_test():
    """监控工具调用"""
    from agents.deepagents import orchestrator

    print("监控: Nginx 502 错误分析")
    print("=" * 60)

    # 使用 astream 来监控每一步
    call_count = 0
    max_calls = 5  # 只监控前 5 步

    async for chunk in orchestrator.astream(
        {"messages": [{"role": "user", "content": "Nginx 502 错误怎么解决？"}]},
        stream_mode="updates"
    ):
        call_count += 1
        print(f"\n[步骤 {call_count}]")
        print(f"数据: {chunk}")

        if call_count >= max_calls:
            print("\n已达到监控上限，停止...")
            break


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.ERROR)  # 只显示错误
    asyncio.run(monitor_test())
