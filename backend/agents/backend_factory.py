"""
Backend 工厂 - 创建和管理 DeepAgents Backend
"""
import logging

logger = logging.getLogger(__name__)


class PatchedCompositeBackend:
    """
    包装 CompositeBackend，修复 write/awrite 返回路径丢失路由前缀的问题。

    CompositeBackend 会将 /memories/xxx.txt strip 为 xxx.txt 传给子 backend，
    但返回的 WriteResult.path 也是 stripped 后的路径，导致模型看到路径不匹配
    而重复调用 write_file。此包装将原始路径回填到返回结果中。
    """

    def __init__(self, composite):
        self._composite = composite

    def __getattr__(self, name):
        return getattr(self._composite, name)

    def write(self, file_path, content):
        res = self._composite.write(file_path, content)
        if res.path is not None and res.error is None:
            res.path = file_path
        return res

    async def awrite(self, file_path, content):
        res = await self._composite.awrite(file_path, content)
        if res.path is not None and res.error is None:
            res.path = file_path
        return res


def make_backend(runtime):
    """
    创建 CompositeBackend 实例（带路径修复补丁）

    实现混合存储策略：
    - 默认路径使用 StateBackend（临时存储，在会话内持久化）
    - /memories/ 路径使用 StoreBackend（持久化存储，跨线程共享）

    Args:
        runtime: ToolRuntime 实例（由 DeepAgents 自动传入）

    Returns:
        PatchedCompositeBackend 实例
    """
    from pathlib import Path
    from deepagents.backends import CompositeBackend, StateBackend, StoreBackend, FilesystemBackend
    from deepagents.backends.store import BackendContext

    def get_memories_namespace(ctx: BackendContext) -> tuple[str, ...]:
        """获取 /memories/ 路径的命名空间，按 user_id 隔离"""
        user_id = getattr(ctx.runtime.context, "user_id", "") if ctx.runtime.context else ""
        return ("memories", user_id or "default")

    # backend/ 目录下的 skills 目录绝对路径
    project_dir = Path(__file__).resolve().parent.parent
    skills_dir = project_dir / "skills"

    composite = CompositeBackend(
        default=StateBackend(runtime),
        routes={
            "/memories/": StoreBackend(runtime, namespace=get_memories_namespace),
            "/memories/shared/": StoreBackend(runtime, namespace=lambda ctx: ("memories-shared",)),
            "/skills/": FilesystemBackend(root_dir=str(skills_dir), virtual_mode=True),
        }
    )
    return PatchedCompositeBackend(composite)
