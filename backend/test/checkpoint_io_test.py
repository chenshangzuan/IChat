"""测试 checkpoint 读写"""
import sys
import asyncio
sys.path.insert(0, '/.')

async def test():
    from common.session_manager import get_session_manager

    sm = get_session_manager()
    await sm._ensure_checkpointer()

    config = await sm.get_config('test-io', 'deepagents')

    test_checkpoint = {
        'id': 'test-io-123',
        'ts': '2025-03-31T10:00:00Z',
        'channel_values': {'messages': [{'role': 'user', 'content': 'Hello'}]},
        'channel_versions': {'messages': '1'},
        'pending_sends': []
    }

    # 保存
    saved = await sm.checkpointer.aput(config, test_checkpoint, {}, {})
    print('✅ 保存成功')

    # 读取
    result = await sm.checkpointer.aget_tuple(saved)
    print('✅ 读取成功')
    print(f'✅ Config: {result.config}')

    # 检查 checkpoint
    if isinstance(result.checkpoint, dict):
        print('✅ Checkpoint 是 dict')
        print(f'✅ ID: {result.checkpoint.get("id")}')
        msg = result.checkpoint.get('channel_values', {}).get('messages', [{}])[0]
        print(f'✅ Message: {msg.get("content")}')
    else:
        print(f'❌ Checkpoint 类型: {type(result.checkpoint)}')

if __name__ == '__main__':
    asyncio.run(test())
