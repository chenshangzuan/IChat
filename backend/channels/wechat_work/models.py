"""企业微信消息 Pydantic 模型"""
from pydantic import BaseModel


class WechatTextMessage(BaseModel):
    to_user_name: str
    from_user_name: str
    create_time: int
    msg_type: str = "text"
    content: str
    msg_id: str
    agent_id: str = ""


class WechatEventMessage(BaseModel):
    to_user_name: str
    from_user_name: str
    create_time: int
    msg_type: str = "event"
    event: str
    agent_id: str = ""
