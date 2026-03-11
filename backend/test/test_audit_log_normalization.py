"""
测试审计日志规范化 Skill

验证 SRE Agent 的 audit-log-normalization 功能
"""
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    stream=sys.stdout,
)


async def test_audit_log_normalization():
    """测试审计日志规范化功能"""
    print("\n" + "=" * 60)
    print("🧪 测试: 审计日志规范化 (Audit Log Normalization)")
    print("=" * 60)

    from demos.deepagents_demo import chat_response

    test_cases = [
        {
            "name": "接口描述规范化",
            "query": "请帮我将接口描述'Query bandwidth cluster usage' 处理成标准接口行为描述"
        },
        {
            "name": "操作符规范化",
            "query": "请帮我将接口操作符'DescribeBandwidthClusterUsage' 处理成标准接口行为描述"
        },
        {
            "name": "格式错误修正",
            "query": "请将 'create_ecs_instance' 规范化为标准接口行为描述"
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 60}")
        print(f"\n📝 用户问题: {test_case['query']}")
        print("-" * 40)

        try:
            response = await chat_response(
                user_input=test_case['query'],
                session_id=f"test-audit-log-{i}"
            )

            print(f"\n✅ SRE Agent 响应:")
            print("=" * 60)
            print(response)
            print("=" * 60)

            # 验证响应是否包含标准格式
            has_standard_format = any(word in response for word in [
                "Describe", "Create", "Update", "Delete", "List", "Monitor",
                "ZEC", "IAM", "DB", "BMC", "Network"
            ])

            if has_standard_format:
                print(f"\n✅ 测试通过: 包含标准格式")
            else:
                print(f"\n⚠️ 警告: 可能未正确应用规范化规则")

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_audit_log_normalization())
