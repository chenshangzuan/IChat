"""
Debug Async Checkpoint Saver

继承标准 AsyncSqliteSaver，序列化/反序列化完全复用 LangGraph 标准 serde（msgpack），
额外在 checkpoints 和 writes 表中增加明文 TEXT 字段，供直接查询 DB 调试使用。
"""
import json
from typing import Any
from collections.abc import Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    Checkpoint,
    CheckpointMetadata,
    ChannelVersions,
    get_checkpoint_metadata,
)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def _to_json_safe(obj: Any) -> Any:
    """将对象转换为 JSON 可序列化的格式（仅用于明文调试字段）"""
    if isinstance(obj, bytes):
        return f"<bytes len={len(obj)}>"
    elif isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]
    elif hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
        try:
            return obj.dict()
        except Exception:
            return str(obj)
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


class DebugAsyncSqliteSaver(AsyncSqliteSaver):
    """
    标准 AsyncSqliteSaver + 明文调试字段

    - 序列化/反序列化：完全复用父类（msgpack），保证正确性
    - 额外字段：checkpoint_text / value_text，存储可读 JSON，仅供调试
    """

    async def setup(self) -> None:
        """创建标准表结构 + 明文调试字段"""
        async with self.lock:
            if self.is_setup:
                return
            await _ensure_connected(self.conn)
            async with self.conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    type TEXT,
                    checkpoint BLOB,
                    metadata BLOB,
                    checkpoint_text TEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                );
                CREATE TABLE IF NOT EXISTS writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    type TEXT,
                    value BLOB,
                    value_text TEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                );
                """
            ):
                await self.conn.commit()
            self.is_setup = True

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """标准写入 + 额外更新明文字段"""
        result = await super().aput(config, checkpoint, metadata, new_versions)

        # 额外写入明文 JSON 调试字段
        try:
            checkpoint_text = json.dumps(
                _to_json_safe(checkpoint), ensure_ascii=False, indent=2
            )
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            async with self.lock:
                await self.conn.execute(
                    "UPDATE checkpoints SET checkpoint_text = ? WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?",
                    (
                        checkpoint_text,
                        str(config["configurable"]["thread_id"]),
                        checkpoint_ns,
                        checkpoint["id"],
                    ),
                )
                await self.conn.commit()
        except Exception:
            pass  # 明文字段写入失败不影响正常功能

        return result

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """标准写入 + 额外更新明文字段"""
        await super().aput_writes(config, writes, task_id, task_path)

        # 额外写入明文 JSON 调试字段
        try:
            async with self.lock:
                for idx, (channel, value) in enumerate(writes):
                    value_text = json.dumps(
                        _to_json_safe(value), ensure_ascii=False, indent=2
                    )
                    await self.conn.execute(
                        "UPDATE writes SET value_text = ? WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? AND task_id = ? AND idx = ?",
                        (
                            value_text,
                            str(config["configurable"]["thread_id"]),
                            str(config["configurable"].get("checkpoint_ns", "")),
                            str(config["configurable"]["checkpoint_id"]),
                            task_id,
                            WRITES_IDX_MAP.get(channel, idx),
                        ),
                    )
                await self.conn.commit()
        except Exception:
            pass  # 明文字段写入失败不影响正常功能


# 兼容：从 aiosqlite 连接获取 _ensure_connected
async def _ensure_connected(conn):
    """确保 aiosqlite 连接已启动"""
    if not conn._running:
        await conn.__aenter__()
