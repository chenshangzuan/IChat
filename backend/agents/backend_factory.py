"""
Backend 工厂 - 创建和管理 DeepAgents Backend
"""
import logging

logger = logging.getLogger(__name__)


def make_backend(runtime):
    """
    创建 CompositeBackend 实例

    实现混合存储策略：
    - 默认路径使用 StateBackend（临时存储，在会话内持久化）
    - /memories/ 路径使用 StoreBackend（持久化存储，跨线程共享）

    Args:
        runtime: ToolRuntime 实例（由 DeepAgents 自动传入）

    Returns:
        CompositeBackend 实例
    """
    from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
    from deepagents.backends.store import BackendContext

    def get_memories_namespace(ctx: BackendContext) -> tuple[str, ...]:
        """获取 /memories/ 路径的命名空间，按 user_id 隔离"""
        user_id = getattr(ctx.runtime.context, "user_id", "") if ctx.runtime.context else ""
        # 必须始终使用二级 namespace，避免 LIKE 'memories%' 前缀匹配到
        # memories-shared 或其他用户的 memories.xxx
        return ("memories", user_id or "default")

    logger.debug("🔧 [BackendFactory] 创建 CompositeBackend")
    logger.debug(f"  - 默认: StateBackend (临时存储)")
    logger.debug(f"  - /memories/: StoreBackend (持久化存储)")

    return CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(runtime, namespace=get_memories_namespace),
            "/memories/shared/": StoreBackend(runtime, namespace=lambda ctx: ("memories-shared",))
        }
    )
