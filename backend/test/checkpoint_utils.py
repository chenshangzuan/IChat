#!/usr/bin/env python3
"""
LangGraph Checkpoint Utilities
工具函数用于反序列化和查看 checkpoint 数据
"""
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
import base64

def decode_checkpoint(checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解码 checkpoint 数据
    """
    decoded = {}
    
    # 基本信息
    decoded['id'] = checkpoint_data.get('id')
    decoded['timestamp'] = checkpoint_data.get('ts')
    
    # 解码 channel_values
    if 'channel_values' in checkpoint_data:
        decoded['channel_values'] = {}
        for channel, value in checkpoint_data['channel_values'].items():
            if isinstance(value, str):
                # 尝试解码 base64 字符串
                try:
                    decoded_value = json.loads(base64.b64decode(value).decode('utf-8'))
                except:
                    decoded_value = value
                decoded['channel_values'][channel] = decoded_value
            else:
                decoded['channel_values'][channel] = value
    
    # channel_versions
    decoded['channel_versions'] = checkpoint_data.get('channel_versions', {})
    
    # pending_sends
    decoded['pending_sends'] = checkpoint_data.get('pending_sends', [])
    
    return decoded

def format_checkpoint_for_display(checkpoint: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    """
    格式化 checkpoint 用于显示
    """
    output = []
    output.append(f"🔍 Checkpoint ID: {checkpoint.get('id', 'N/A')}")
    output.append(f"⏰ Timestamp: {checkpoint.get('timestamp', 'N/A')}")
    output.append(f"📝 Source: {metadata.get('source', 'N/A')}")
    output.append(f"📈 Step: {metadata.get('step', 'N/A')}")
    output.append(f"🔄 Parent: {metadata.get('parents', {}).get('configurable', {}).get('checkpoint_id', 'N/A')}")
    
    # 显示消息
    if 'channel_values' in checkpoint:
        messages = checkpoint['channel_values'].get('messages', [])
        if messages:
            output.append(f"\n💬 Messages ({len(messages)}):")
            for i, msg in enumerate(messages[-10:]):  # 只显示最后10条
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                if len(content) > 100:
                    content = content[:100] + '...'
                output.append(f"  [{len(messages)-len(messages)+i}] {role}: {content}")
    
    # 显示其他 channels
    other_channels = {k: v for k, v in checkpoint.get('channel_values', {}).items() if k != 'messages'}
    if other_channels:
        output.append(f"\n📦 Other Channels:")
        for channel, value in other_channels.items():
            if isinstance(value, (list, dict)) and len(str(value)) > 100:
                output.append(f"  {channel}: {type(value).__name__} with {len(value)} items")
            else:
                output.append(f"  {channel}: {str(value)[:50]}...")
    
    return '\n'.join(output)

def generate_checkpoint_insights():
    """生成 checkpoint 分析的洞察"""
    insights = {
        "storage_format": {
            "serialization": "JSON stored as BLOB",
            "compression": "None (plain JSON)",
            "structure": "Hierarchical with channels",
            "versioning": "Incremental via channel_versions"
        },
        "retrieval_methods": [
            "By thread_id (latest)",
            "By thread_id and checkpoint_id",
            "By metadata filters",
            "By timestamp range"
        ],
        "data_flow": {
            "user_input": "Stored in messages channel",
            "ai_response": "Stored in messages channel",
            "intermediate_steps": "Stored in writes table",
            "state": "Stored in channel_values"
        },
        "best_practices": {
            "regular_cleanup": "Delete old checkpoints to save space",
            "metadata_indexing": "Add indexes on metadata columns for performance",
            "backup": "Regular database backups",
            "monitoring": "Track checkpoint growth over time"
        }
    }
    
    print("\n📊 LangGraph Checkpoint Insights:")
    print("=" * 60)
    
    for category, data in insights.items():
        print(f"\n🔍 {category.replace('_', ' ').title()}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"   • {key}: {value}")
        elif isinstance(data, list):
            for item in data:
                print(f"   • {item}")
    
    print("\n💡 Pro Tips:")
    print("1. 使用 thread_id 进行会话隔离")
    print("2. 定期清理旧的 checkpoints 以保持性能")
    print("3. 可以通过 metadata 实现自定义查询")
    print("4. 考虑实现 checkpoint 的定期导出备份")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LangGraph Checkpoint Utilities')
    parser.add_argument('--insights', action='store_true', help='Generate insights')
    
    args = parser.parse_args()
    
    if args.insights:
        generate_checkpoint_insights()
    else:
        print("Use --insights")