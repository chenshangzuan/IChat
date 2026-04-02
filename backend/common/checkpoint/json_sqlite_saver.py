"""
自定义 Async Checkpoint Saver，将 checkpoint 存储为明文 JSON TEXT

直接将 checkpoint 数据序列化为可读的 JSON 字符串存储，
不使用 msgpack 编码，便于直接查看和调试。
"""
import json
from typing import Any, Optional, cast
from collections.abc import AsyncIterator

import aiosqlite
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    get_checkpoint_id,
    get_checkpoint_metadata,
    BaseCheckpointSaver,
)


def _serialize_value(obj: Any) -> Any:
    """将对象转换为 JSON 可序列化的格式"""
    if isinstance(obj, bytes):
        # base64 编码 bytes
        import base64
        return {"__type__": "bytes", "data": base64.b64encode(obj).decode('ascii')}
    elif isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_value(v) for v in obj]
    elif isinstance(obj, tuple):
        return {"__type__": "tuple", "data": [_serialize_value(v) for v in obj]}
    else:
        # 处理 LangChain 消息对象
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
            try:
                return obj.dict()
            except:
                pass

        # 尝试直接序列化，失败则转为字符串
        try:
            json.dumps(obj)
            return obj
        except:
            return str(obj)


class AsyncJsonSqliteSaver(BaseCheckpointSaver):
    """
    将 checkpoint 存储为可读 JSON TEXT 的 CheckpointSaver

    不使用 msgpack 编码，直接将 checkpoint 数据序列化为可读的 JSON。
    不继承 AsyncSqliteSaver，完全独立实现以避免 schema 冲突。
    """
    def __init__(self, conn: aiosqlite.Connection):
        """
        初始化 AsyncJsonSqliteSaver

        Args:
            conn: aiosqlite 连接对象
        """
        import asyncio
        self.conn = conn
        self.lock = asyncio.Lock()
        self.is_setup = False

    async def setup(self) -> None:
        """创建使用 TEXT 类型的表结构"""
        async with self.lock:
            if self.is_setup:
                return

            await self.conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    checkpoint TEXT,
                    metadata TEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                );
                CREATE TABLE IF NOT EXISTS writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    value TEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                );
                """
            )
            self.is_setup = True

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """获取 checkpoint tuple，从 JSON 字符串恢复"""
        await self.setup()
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        async with self.lock, self.conn.cursor() as cur:
            if checkpoint_id := get_checkpoint_id(config):
                await cur.execute(
                    "SELECT thread_id, checkpoint_id, parent_checkpoint_id, checkpoint, metadata FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?",
                    (
                        str(config["configurable"]["thread_id"]),
                        checkpoint_ns,
                        checkpoint_id,
                    ),
                )
            else:
                await cur.execute(
                    "SELECT thread_id, checkpoint_id, parent_checkpoint_id, checkpoint, metadata FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? ORDER BY checkpoint_id DESC LIMIT 1",
                    (str(config["configurable"]["thread_id"]), checkpoint_ns),
                )

            if value := await cur.fetchone():
                (
                    thread_id,
                    checkpoint_id,
                    parent_checkpoint_id,
                    checkpoint_json,
                    metadata_json,
                ) = value

                if not get_checkpoint_id(config):
                    config = {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": checkpoint_id,
                        }
                    }

                # 查找 writes
                await cur.execute(
                    "SELECT task_id, channel, value FROM writes WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? ORDER BY task_id, idx",
                    (
                        str(config["configurable"]["thread_id"]),
                        checkpoint_ns,
                        str(config["configurable"]["checkpoint_id"]),
                    ),
                )

                # 反序列化 checkpoint
                if checkpoint_json:
                    checkpoint = json.loads(checkpoint_json)
                else:
                    checkpoint = {}

                # 反序列化 metadata
                metadata = (
                    json.loads(metadata_json)
                    if metadata_json is not None
                    else {}
                )

                # 反序列化 writes
                writes = []
                async for task_id, channel, value_json in cur:
                    if value_json:
                        value = json.loads(value_json)
                    else:
                        value = None
                    writes.append((task_id, channel, value))

                return CheckpointTuple(
                    config,
                    checkpoint,
                    cast(CheckpointMetadata, metadata),
                    (
                        {
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": checkpoint_ns,
                                "checkpoint_id": parent_checkpoint_id,
                            }
                        }
                        if parent_checkpoint_id
                        else None
                    ),
                    writes,
                )
            return None

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """保存 checkpoint，直接存储为可读 JSON"""
        await self.setup()
        async with self.lock:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

            # 直接序列化为可读 JSON（不使用 serde）
            serializable_checkpoint = _serialize_value(checkpoint)
            checkpoint_json = json.dumps(serializable_checkpoint, ensure_ascii=False, indent=2)

            metadata_dict = get_checkpoint_metadata(config, metadata)
            metadata_json = json.dumps(metadata_dict, ensure_ascii=False, indent=2)

            await self.conn.execute(
                """INSERT OR REPLACE INTO checkpoints
                   (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                    checkpoint, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(thread_id),
                    checkpoint_ns,
                    checkpoint["id"],
                    config["configurable"].get("checkpoint_id"),
                    checkpoint_json,
                    metadata_json,
                ),
            )
            await self.conn.commit()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: list[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """保存 writes，直接存储为可读 JSON"""
        await self.setup()
        async with self.lock, self.conn.cursor() as cur:
            for idx, (channel, value) in enumerate(writes):
                serializable_value = _serialize_value(value)
                value_json = json.dumps(serializable_value, ensure_ascii=False, indent=2)

                await cur.execute(
                    """INSERT OR REPLACE INTO writes
                       (thread_id, checkpoint_ns, checkpoint_id, task_id,
                        idx, channel, value)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(config["configurable"]["thread_id"]),
                        str(config["configurable"].get("checkpoint_ns", "")),
                        str(config["configurable"]["checkpoint_id"]),
                        task_id,
                        WRITES_IDX_MAP.get(channel, idx),
                        channel,
                        value_json,
                    ),
                )
            await self.conn.commit()

    # 实现必需的抽象方法
    async def alist(
        self,
        config: RunnableConfig,
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """列出所有 checkpoints"""
        await self.setup()
        # 简化实现，仅返回基本功能
        return
        yield  # 使其成为异步生成器

    async def adelete(self, config: RunnableConfig) -> None:
        """删除 checkpoint"""
        await self.setup()
        async with self.lock:
            thread_id = str(config["configurable"]["thread_id"])
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            checkpoint_id = get_checkpoint_id(config)

            if checkpoint_id:
                await self.conn.execute(
                    "DELETE FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?",
                    (thread_id, checkpoint_ns, checkpoint_id),
                )
            else:
                await self.conn.execute(
                    "DELETE FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ?",
                    (thread_id, checkpoint_ns),
                )
            await self.conn.commit()
