"""
Checkpoint 查看工具 - 简化版

直接查看 SQLite 中存储的 checkpoint JSON 数据。
"""
import json
import sys
import aiosqlite
import asyncio
from pathlib import Path


async def view_checkpoints(db_path: str = "data/deepagent_demo.db", limit: int = 5):
    """查看 checkpoints 表中的数据"""
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return

    conn = await aiosqlite.connect(db_path)

    print("=" * 80)
    print(f"📊 Checkpoint 数据库: {db_path}")
    print("=" * 80)

    # 获取所有 checkpoints
    async with conn.execute(
        "SELECT thread_id, checkpoint_id, checkpoint, metadata FROM checkpoints ORDER BY rowid DESC LIMIT ?",
        (limit,)
    ) as cur:
        rows = await cur.fetchall()

    if not rows:
        print("\n📭 暂无 checkpoint 数据")
        print("   提示: 发送聊天消息后会自动创建 checkpoint")
    else:
        print(f"\n📋 找到 {len(rows)} 条 checkpoint 记录:\n")

        for i, (thread_id, checkpoint_id, checkpoint_json, metadata_json) in enumerate(rows, 1):
            print(f"{'─' * 80}")
            print(f"🔹 [{i}] Thread ID: {thread_id}")
            print(f"   Checkpoint ID: {checkpoint_id}")

            # 解析并显示 checkpoint
            if checkpoint_json:
                try:
                    checkpoint = json.loads(checkpoint_json)
                    print(f"   📦 Checkpoint:")

                    # 显示主要字段
                    if "id" in checkpoint:
                        print(f"      - id: {checkpoint['id']}")
                    if "ts" in checkpoint:
                        print(f"      - ts: {checkpoint['ts']}")

                    # 显示 channel_values 中的 messages
                    if "channel_values" in checkpoint:
                        channel_values = checkpoint["channel_values"]
                        if "messages" in channel_values:
                            messages = channel_values["messages"]
                            print(f"      - messages: {len(messages)} 条")
                            for msg in messages[-3:]:  # 只显示最后 3 条
                                if isinstance(msg, dict):
                                    role = msg.get("role", "unknown")
                                    content = msg.get("content", "")
                                    content_preview = content[:100] + "..." if len(content) > 100 else content
                                    print(f"          - [{role}]: {content_preview}")

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON 解析失败: {e}")
                    print(f"   📄 原始数据（前 200 字符）: {checkpoint_json[:200]}...")

            # 显示 metadata
            if metadata_json:
                try:
                    metadata = json.loads(metadata_json)
                    if metadata:
                        print(f"   🏷️  Metadata: {json.dumps(metadata, ensure_ascii=False)}")
                except json.JSONDecodeError:
                    pass

            print()

    # 获取 writes 数据
    async with conn.execute(
        "SELECT thread_id, checkpoint_id, task_id, channel, value FROM writes ORDER BY rowid DESC LIMIT ?",
        (limit,)
    ) as cur:
        writes = await cur.fetchall()

    if writes:
        print(f"{'─' * 80}")
        print(f"📝 Writes 数据 ({len(writes)} 条):")
        for i, (thread_id, checkpoint_id, task_id, channel, value_json) in enumerate(writes[:5], 1):
            print(f"   [{i}] {thread_id} | {channel} | {task_id}")
            if value_json and len(value_json) < 500:
                # 尝试解析并格式化显示
                try:
                    value = json.loads(value_json)
                    if isinstance(value, dict) and len(str(value)) < 300:
                        print(f"       {json.dumps(value, ensure_ascii=False)}")
                    else:
                        print(f"       {value_json[:100]}...")
                except:
                    print(f"       {value_json[:100]}...")
        print()

    await conn.close()

    print("=" * 80)
    print("\n💡 提示: 可以直接用 SQLite 命令查看数据:")
    print(f"  sqlite3 {db_path} \"SELECT checkpoint FROM checkpoints LIMIT 1;\"")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="查看 LangGraph checkpoint 数据")
    parser.add_argument("--db", default="data/deepagent_demo.db", help="数据库文件路径")
    parser.add_argument("--limit", type=int, default=5, help="显示的记录数量")
    args = parser.parse_args()

    await view_checkpoints(args.db, args.limit)


if __name__ == "__main__":
    asyncio.run(main())
