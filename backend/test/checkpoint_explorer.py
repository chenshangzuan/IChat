#!/usr/bin/env python3
"""
LangGraph Checkpoint Explorer Tool
探索 LangGraph 在 SQLite 中的 checkpoint 数据
"""
import json
import sqlite3
import argparse
import sys
from pathlib import Path

def get_database_path():
    """获取数据库文件路径"""
    return Path("data/deepagent_demo.db")

def view_checkpoints(db_path):
    """查看所有 checkpoint"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("📊 LangGraph Checkpoints Database Explorer")
    print("=" * 80)
    
    # 查看所有线程
    cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
    threads = cursor.fetchall()
    
    if not threads:
        print("📋 数据库为空，没有找到 checkpoints")
        return
    
    for (thread_id,) in threads:
        print(f"\n🧵 Thread ID: {thread_id}")
        print("-" * 50)
        
        # 查询该线程的所有 checkpoints
        cursor.execute('''
        SELECT checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata
        FROM checkpoints 
        WHERE thread_id = ?
        ORDER BY checkpoint_id DESC
        ''', (thread_id,))
        
        checkpoints = cursor.fetchall()
        
        for (checkpoint_id, parent_id, type_, checkpoint_blob, metadata_json) in checkpoints:
            print(f"\n🔍 Checkpoint ID: {checkpoint_id}")
            print(f"   Parent ID: {parent_id or 'None'}")
            print(f"   Type: {type_}")
            
            # 解析 checkpoint 数据
            try:
                checkpoint_data = json.loads(checkpoint_blob) if checkpoint_blob else {}
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                print(f"   📅 Timestamp: {checkpoint_data.get('ts', 'N/A')}")
                print(f"   📊 Channel Count: {len(checkpoint_data.get('channel_versions', {}))}")
                print(f"   📦 Messages: {len(checkpoint_data.get('channel_values', {}).get('messages', []))}")
                print(f"   📝 Source: {metadata.get('source', 'N/A')}")
                print(f"   📈 Step: {metadata.get('step', 'N/A')}")
                
                # 显示前3条消息
                messages = checkpoint_data.get('channel_values', {}).get('messages', [])
                if messages:
                    print("   💬 Recent Messages:")
                    for i, msg in enumerate(messages[-3:]):
                        print(f"     [{i}] {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")
                
            except Exception as e:
                print(f"   ⚠️ Error parsing checkpoint: {e}")
    
    conn.close()

def analyze_checkpoint_structure():
    """分析 checkpoint 的数据结构"""
    print("\n" + "=" * 80)
    print("🔬 LangGraph Checkpoint Structure Analysis")
    print("=" * 80)
    
    # 基于源码分析的表结构
    schema = {
        "checkpoints_table": {
            "table": "checkpoints",
            "columns": [
                {"name": "thread_id", "type": "TEXT", "description": "会话标识符"},
                {"name": "checkpoint_ns", "type": "TEXT", "default": "''", "description": "checkpoint 命名空间"},
                {"name": "checkpoint_id", "type": "TEXT", "description": "checkpoint 唯一ID"},
                {"name": "parent_checkpoint_id", "type": "TEXT", "nullable": True, "description": "父 checkpoint ID"},
                {"name": "type", "type": "TEXT", "description": "checkpoint 数据类型（通常是 'json'）"},
                {"name": "checkpoint", "type": "BLOB", "description": "序列化后的 checkpoint 数据"},
                {"name": "metadata", "type": "TEXT", "description": "元数据（JSON格式）"}
            ],
            "primary_key": ["thread_id", "checkpoint_ns", "checkpoint_id"]
        },
        "writes_table": {
            "table": "writes",
            "columns": [
                {"name": "thread_id", "type": "TEXT", "description": "会话标识符"},
                {"name": "checkpoint_ns", "type": "TEXT", "default": "''", "description": "checkpoint 命名空间"},
                {"name": "checkpoint_id", "type": "TEXT", "description": "关联的 checkpoint ID"},
                {"name": "task_id", "type": "TEXT", "description": "任务ID"},
                {"name": "idx", "type": "INTEGER", "description": "写入索引"},
                {"name": "channel", "type": "TEXT", "description": "通道名称"},
                {"name": "type", "type": "TEXT", "description": "数据类型"},
                {"name": "value", "type": "BLOB", "description": "写入的值"}
            ],
            "primary_key": ["thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx"]
        }
    }
    
    print("\n📋 数据库表结构:")
    for table_name, table_info in schema.items():
        print(f"\n📂 {table_info['table']}:")
        for col in table_info['columns']:
            default_info = f" (default: {col['default']})" if 'default' in col else ""
            nullable_info = " (nullable)" if col.get('nullable') else ""
            print(f"   - {col['name']}: {col['type']}{default_info}{nullable_info}")
            print(f"     {col['description']}")
        
        if 'primary_key' in table_info:
            print(f"   🔑 Primary Key: {', '.join(table_info['primary_key'])}")
    
    print("\n🔧 使用说明:")
    print("1. checkpoint 表存储了完整的状态快照")
    print("2. writes 表存储了中间的写入操作")
    print("3. 每个 checkpoint 有一个唯一的 ID")
    print("4. thread_id 通常格式为 'demo_id:session_id'")
    
    # 示例 checkpoint 数据结构
    print("\n💾 Checkpoint 数据结构示例:")
    example_checkpoint = {
        "id": "checkpoint-uuid",
        "ts": "2023-05-03T10:00:00Z",
        "channel_values": {
            "messages": [
                {"role": "user", "content": "用户消息"},
                {"role": "assistant", "content": "AI回复"}
            ],
            "some_channel": "some_value"
        },
        "channel_versions": {
            "messages": "1",
            "some_channel": "1"
        },
        "pending_sends": []
    }
    
    print(json.dumps(example_checkpoint, indent=2, ensure_ascii=False))
    
    # 示例元数据
    print("\n📝 Metadata 结构示例:")
    example_metadata = {
        "source": "user",
        "step": 0,
        "writes": {},
        "parents": {
            "configurable": {
                "thread_id": "parent-thread-id",
                "checkpoint_id": "parent-checkpoint-id"
            }
        }
    }
    
    print(json.dumps(example_metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LangGraph Checkpoint Explorer')
    parser.add_argument('--view', action='store_true', help='View all checkpoints')
    parser.add_argument('--structure', action='store_true', help='Analyze checkpoint structure')
    
    args = parser.parse_args()
    
    db_path = get_database_path()
    
    if args.view:
        if db_path.exists():
            view_checkpoints(str(db_path))
        else:
            print(f"❌ Database not found at {db_path}")
            print("请确保数据库文件已创建")
    elif args.structure:
        analyze_checkpoint_structure()
    else:
        print("No action specified. Use --help for options.")
        print("\n示例:")
        print("  python3 checkpoint_explorer.py --view")      # 查看现有 checkpoints
        print("  python3 checkpoint_explorer.py --structure")  # 分析数据结构
