"""
企业微信自建应用回调接口

GET  /channels/wechat_work  — 服务器验证（echostr 回显）
POST /channels/wechat_work  — 接收消息（立即 200，BackgroundTask 异步处理）
"""
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from channels.wechat_work.auth import decrypt_message, parse_xml_message, verify_signature
from channels.wechat_work.handler import get_wechat_work_handler
from channels.wechat_work.models import WechatEventMessage, WechatTextMessage
from common.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels/wechat_work", tags=["企业微信"])


@router.get("")
async def verify_server(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    """
    企业微信服务器验证（安全模式）：
    1. 签名 = SHA1(sort(token, timestamp, nonce, echostr_encrypted))
    2. 解密 echostr，原样返回明文
    """
    if not verify_signature(config.WECHAT_WORK_TOKEN, timestamp, nonce, msg_signature, echostr):
        raise HTTPException(status_code=403, detail="签名验证失败")

    plain = decrypt_message(echostr, config.WECHAT_WORK_ENCODING_AES_KEY, config.WECHAT_WORK_CORP_ID)
    logger.info("[WechatWork] 服务器验证通过")
    return PlainTextResponse(content=plain)


@router.post("")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
):
    """
    接收企业微信消息回调。
    立即返回空串（满足 5 秒响应要求），异步处理消息后通过 API 主动推送回复。
    """
    body = await request.body()
    xml_str = body.decode("utf-8")

    # 先拿到 Encrypt 字段，再做 4 参数签名验证
    fields = parse_xml_message(xml_str)
    encrypt_msg = fields.get("Encrypt", "")

    if not verify_signature(config.WECHAT_WORK_TOKEN, timestamp, nonce, msg_signature, encrypt_msg):
        raise HTTPException(status_code=403, detail="签名验证失败")

    if not encrypt_msg:
        # 未加密模式（明文模式，开发调试用）
        msg_xml = xml_str
    else:
        try:
            msg_xml = decrypt_message(
                encrypt_msg,
                config.WECHAT_WORK_ENCODING_AES_KEY,
                config.WECHAT_WORK_CORP_ID,
            )
        except Exception as e:
            logger.error(f"[WechatWork] 消息解密失败: {e}")
            return ""

    fields = parse_xml_message(msg_xml)
    msg_type = fields.get("MsgType", "").lower()
    from_user = fields.get("FromUserName", "")
    to_user = fields.get("ToUserName", "")
    create_time = int(fields.get("CreateTime", "0"))
    agent_id = fields.get("AgentID", "")

    handler = get_wechat_work_handler()

    if msg_type == "text":
        msg = WechatTextMessage(
            to_user_name=to_user,
            from_user_name=from_user,
            create_time=create_time,
            content=fields.get("Content", ""),
            msg_id=fields.get("MsgId", ""),
            agent_id=agent_id,
        )
        background_tasks.add_task(handler.handle, msg)

    elif msg_type == "event":
        msg = WechatEventMessage(
            to_user_name=to_user,
            from_user_name=from_user,
            create_time=create_time,
            event=fields.get("Event", ""),
            agent_id=agent_id,
        )
        background_tasks.add_task(handler.handle, msg)

    else:
        logger.debug(f"[WechatWork] 忽略消息类型: {msg_type}")

    return ""
