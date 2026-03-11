"""
快速测试修复后的效果
"""
import asyncio
from demos.deepagents_demo import chat_response_with_metadata

async def test():
    print("测试: 帮我写一个java的冒泡排序")
    print("=" * 60)

    result = await chat_response_with_metadata(
        user_input='帮我写一个java的冒泡排序',
        session_id='final-test'
    )

    response = result['response']
    agent = result['agent']

    print(f"\nAgent 类型: {agent}")
    print(f"响应长度: {len(response)} 字符")
    print(f"包含代码块: {'```' in response}")
    print(f"包含 'java' 关键字: {'java' in response.lower()}")

    if len(response) < 100:
        print("\n⚠️ 响应太短，可能有问题:")
        print(response)
    else:
        print(f"\n✅ 响应正常！")
        print(f"\n前300字符预览:")
        print(response[:300])
        print(f"\n...（还有 {len(response) - 300} 字符）")

if __name__ == "__main__":
    asyncio.run(test())
