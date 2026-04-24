"""
Channel 抽象基类

所有 channel（企业微信、Slack、钉钉等）继承此类，实现 send_text / send_markdown。
公共逻辑（流式处理、session 生成、审批状态机）在此实现，子类直接复用。
"""
import asyncio
import json
import logging
from abc import ABC, abstractmethod

from common.config import config

logger = logging.getLogger(__name__)

# 审批关键词
_APPROVE_KEYWORDS = {"同意", "approve", "yes", "是", "确认", "ok"}
_REJECT_KEYWORDS = {"拒绝", "reject", "no", "否", "取消", "cancel"}


class BaseChannel(ABC):
    channel_id: str

    def __init__(self):
        # session_id → {"actions": [...], "timestamp": str}
        self._pending_approvals: dict[str, dict] = {}

    def make_session_id(self, from_user: str, party_id: str = "") -> str:
        if party_id:
            return f"{self.channel_id}:group:{party_id}:{from_user}"
        return f"{self.channel_id}:{from_user}"

    async def handle_text(self, from_user: str, content: str, party_id: str = "") -> None:
        """统一文本消息入口：优先检查 pending approval，再走正常聊天"""
        session_id = self.make_session_id(from_user, party_id)
        content = content.strip()

        if session_id in self._pending_approvals:
            lower = content.lower()
            if lower in _APPROVE_KEYWORDS:
                asyncio.create_task(self._run_approve(session_id, from_user, "approve"))
                return
            elif lower in _REJECT_KEYWORDS:
                asyncio.create_task(self._run_approve(session_id, from_user, "reject", content))
                return
            else:
                await self.send_text(from_user, "⚠️ 有待审批的操作，请先回复「同意」或「拒绝」。")
                return

        asyncio.create_task(self._run_stream(session_id, content, from_user))

    async def _run_stream(self, session_id: str, user_input: str, recipient: str) -> None:
        """调用 DeepAgent 流，汇总结果后发送给用户"""
        from demos import deepagents_chat

        try:
            response_buf = []
            tool_notified = False

            async def _stream():
                nonlocal tool_notified
                async for raw_chunk in deepagents_chat.chat_stream_with_metadata(
                    user_input=user_input,
                    session_id=session_id,
                    user_id=recipient,
                ):
                    yield raw_chunk

            async with asyncio.timeout(config.CHANNEL_TIMEOUT):
                async for chunk in _stream():
                    chunk_str = chunk if isinstance(chunk, str) else chunk.decode()

                    # 解析 SSE 帧
                    for line in chunk_str.splitlines():
                        if line.startswith("event: tool_call"):
                            if not tool_notified:
                                await self.send_text(recipient, "🔧 正在调用工具，请稍候...")
                                tool_notified = True
                        elif line.startswith("event: approval"):
                            pass  # approval data 在下一行，由 data: 处理
                        elif line.startswith("event: metadata") or line.startswith("event: error"):
                            pass
                        elif line.startswith("data: "):
                            data = line[6:]
                            # 尝试解析结构化事件
                            if data.startswith("{"):
                                try:
                                    obj = json.loads(data)
                                    event_type = obj.get("type", "")
                                    if event_type == "approval_request":
                                        await self._handle_approval_event(session_id, recipient, obj)
                                        return  # 等待用户审批，不发送最终响应
                                    # tool_call / metadata → 忽略文本累积
                                except json.JSONDecodeError:
                                    response_buf.append(data)
                            else:
                                response_buf.append(data)

            final_text = "".join(response_buf).strip()
            if final_text:
                await self.send_text(recipient, final_text)

        except TimeoutError:
            logger.error(f"[{self.channel_id}] DeepAgent timeout: session={session_id}")
            await self.send_text(recipient, "⏱️ 处理超时，请重试。")
        except Exception as e:
            logger.error(f"[{self.channel_id}] Stream error: {e}")
            await self.send_text(recipient, f"❌ 出错了：{e}")

    async def _handle_approval_event(self, session_id: str, recipient: str, obj: dict) -> None:
        """处理审批事件：记录 pending + 发送提示给用户"""
        actions = obj.get("actions", [])
        self._pending_approvals[session_id] = {"actions": actions}

        lines = ["🔔 **Agent 请求执行以下操作，请确认：**\n"]
        for i, action in enumerate(actions, 1):
            name = action.get("name", "unknown")
            desc = action.get("description", "")
            args = action.get("args", {})
            lines.append(f"**{i}. {name}**")
            if desc:
                lines.append(f"   说明：{desc}")
            if args:
                for k, v in args.items():
                    lines.append(f"   - {k}: {v}")
        lines.append("\n回复「**同意**」继续执行，或「**拒绝**」取消。")

        await self.send_markdown(recipient, "\n".join(lines))

    async def _run_approve(
        self, session_id: str, recipient: str, decision: str, reason: str = ""
    ) -> None:
        """执行审批恢复"""
        from demos import deepagents_chat

        self._pending_approvals.pop(session_id, None)

        decisions = [{"type": decision, "message": reason or "用户拒绝了此操作"}]
        try:
            response_buf = []

            async with asyncio.timeout(config.CHANNEL_TIMEOUT):
                async for chunk in deepagents_chat.chat_approve_stream(
                    session_id=session_id,
                    user_id=recipient,
                    decisions=decisions,
                ):
                    chunk_str = chunk if isinstance(chunk, str) else chunk.decode()
                    for line in chunk_str.splitlines():
                        if line.startswith("data: ") and not line[6:].startswith("{"):
                            response_buf.append(line[6:])

            final_text = "".join(response_buf).strip()
            if final_text:
                await self.send_text(recipient, final_text)
            else:
                status = "✅ 已同意" if decision == "approve" else "❌ 已拒绝"
                await self.send_text(recipient, status)

        except TimeoutError:
            await self.send_text(recipient, "⏱️ 审批恢复超时，请重试。")
        except Exception as e:
            logger.error(f"[{self.channel_id}] Approve error: {e}")
            await self.send_text(recipient, f"❌ 审批处理失败：{e}")

    @abstractmethod
    async def send_text(self, recipient: str, content: str) -> None: ...

    @abstractmethod
    async def send_markdown(self, recipient: str, content: str) -> None: ...
