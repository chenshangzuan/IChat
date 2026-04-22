"""
企业微信 API 客户端

- WechatWorkTokenManager: access_token 获取与缓存（有效期 2h，提前 5min 刷新）
- WechatWorkClient: 发送文本 / markdown 消息
"""
import asyncio
import logging
import time

import httpx

from common.config import config

logger = logging.getLogger(__name__)

_QYAPI_BASE = "https://qyapi.weixin.qq.com/cgi-bin"


class WechatWorkTokenManager:
    """单例 access_token 管理器，自动刷新"""

    def __init__(self):
        self._token: str = ""
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        async with self._lock:
            if time.time() < self._expires_at - 300:  # 提前 5 分钟刷新
                return self._token
            await self._refresh()
            return self._token

    async def _refresh(self) -> None:
        url = f"{_QYAPI_BASE}/gettoken"
        params = {
            "corpid": config.WECHAT_WORK_CORP_ID,
            "corpsecret": config.WECHAT_WORK_AGENT_SECRET,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"获取 access_token 失败: {data}")

        self._token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 7200)
        logger.info("[WechatWork] access_token 已刷新")


_token_manager = WechatWorkTokenManager()


class WechatWorkClient:
    """向企业微信用户发送消息"""

    async def send_text(self, user_id: str, content: str) -> None:
        await self._send({
            "touser": user_id,
            "msgtype": "text",
            "agentid": config.WECHAT_WORK_AGENT_ID,
            "text": {"content": content},
        })

    async def send_markdown(self, user_id: str, content: str) -> None:
        await self._send({
            "touser": user_id,
            "msgtype": "markdown",
            "agentid": config.WECHAT_WORK_AGENT_ID,
            "markdown": {"content": content},
        })

    async def _send(self, payload: dict) -> None:
        token = await _token_manager.get_token()
        url = f"{_QYAPI_BASE}/message/send"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, params={"access_token": token}, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if data.get("errcode", 0) != 0:
            logger.error(f"[WechatWork] 发消息失败: {data}")
        else:
            logger.debug(f"[WechatWork] 消息已发送给 {payload.get('touser')}")
