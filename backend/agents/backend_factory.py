"""
Backend 工厂 - 创建和管理 DeepAgents Backend
"""
import logging
from pathlib import Path

from deepagents.backends import CompositeBackend, StoreBackend, FilesystemBackend, LocalShellBackend
from deepagents.backends.store import BackendContext

logger = logging.getLogger(__name__)

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_SKILLS_DIR = _PROJECT_DIR / "skills"


class PatchedCompositeBackend(CompositeBackend):
    """
    CompositeBackend 子类，修复 write/awrite 返回路径丢失路由前缀的问题。

    CompositeBackend 会将 /memories/xxx.txt strip 为 xxx.txt 传给子 backend，
    但返回的 WriteResult.path 也是 stripped 后的路径，导致模型看到路径不匹配
    而重复调用 write_file。此子类将原始路径回填到返回结果中。

    继承 CompositeBackend 而非简单包装，确保 isinstance 检查（如
    _supports_execution 对 SandboxBackendProtocol 的判断）能正常工作。
    """

    def write(self, file_path, content):
        res = super().write(file_path, content)
        if res.path is not None and res.error is None:
            res.path = file_path
        return res

    async def awrite(self, file_path, content):
        res = await super().awrite(file_path, content)
        if res.path is not None and res.error is None:
            res.path = file_path
        return res


def make_backend(runtime):
    """
    创建 PatchedCompositeBackend 实例。

    存储策略：
    - 默认路径：LocalShellBackend（支持 execute 工具执行 shell 命令）
    - /memories/：StoreBackend（持久化存储，按 user_id 隔离）
    - /skills/：FilesystemBackend（只读挂载 skills 目录）

    Args:
        runtime: ToolRuntime 实例（由 DeepAgents 自动传入）

    Returns:
        PatchedCompositeBackend 实例
    """
    def get_memories_namespace(ctx: BackendContext) -> tuple[str, ...]:
        user_id = getattr(ctx.runtime.context, "user_id", "") if ctx.runtime.context else ""
        return ("memories", user_id or "default")

    return PatchedCompositeBackend(
        default=LocalShellBackend(root_dir=str(_PROJECT_DIR), virtual_mode=True, inherit_env=True),
        routes={
            "/memories/": StoreBackend(runtime, namespace=get_memories_namespace),
            "/memories/shared/": StoreBackend(runtime, namespace=lambda ctx: ("memories-shared",)),
            "/skills/": FilesystemBackend(root_dir=str(_SKILLS_DIR), virtual_mode=True)
        }
    )
