"""
企业微信消息处理器

继承 BaseChannel，实现 send_text / send_markdown，
并提供 handle() 方法将企业微信消息分发到公共处理逻辑。
"""
import logging

from channels.base import BaseChannel
from channels.wechat_work.client import WechatWorkClient
from channels.wechat_work.models import WechatEventMessage, WechatTextMessage

logger = logging.getLogger(__name__)


class WechatWorkHandler(BaseChannel):
    channel_id = "wechat_work"

    def __init__(self):
        super().__init__()
        self._client = WechatWorkClient()

    async def handle(self, msg: WechatTextMessage | WechatEventMessage) -> None:
        if isinstance(msg, WechatTextMessage):
            logger.info(f"[WechatWork] 收到文本消息: from={msg.from_user_name}, content={msg.content[:50]}")
            await self.handle_text(
                from_user=msg.from_user_name,
                content=msg.content,
            )
        elif isinstance(msg, WechatEventMessage):
            logger.info(f"[WechatWork] 收到事件: from={msg.from_user_name}, event={msg.event}")
            if msg.event.lower() == "subscribe":
                await self.send_text(msg.from_user_name, "👋 你好！我是 AI 助手，有什么可以帮你？")
        else:
            logger.debug(f"[WechatWork] 忽略未知消息类型: {type(msg)}")

    async def send_text(self, recipient: str, content: str) -> None:
        await self._client.send_text(recipient, content)

    async def send_markdown(self, recipient: str, content: str) -> None:
        await self._client.send_markdown(recipient, content)


# 全局单例
_handler: WechatWorkHandler | None = None


def get_wechat_work_handler() -> WechatWorkHandler:
    global _handler
    if _handler is None:
        _handler = WechatWorkHandler()
    return _handler
