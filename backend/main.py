"""
IChat FastAPI 服务器

提供 Multi-Agent 系统的 API 接口
"""
import logging
from typing import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from common.config import config
from demos import basic_chat, deepagents_demo

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: str = "default"
    demo_id: str = "deepagents"  # 新增：指定使用的 demo


class AgentMetadata(BaseModel):
    """Agent 元数据模型"""
    agent_type: str | None = None  # agent 类型：orchestrator, coder, sre
    delegations: int = 0  # 委托次数
    tool_calls: int = 0  # 工具调用次数
    skill_calls: int = 0  # skill 调用次数
    skills: list[str] = []  # 使用的 skill 名称列表
    duration: float = 0.0  # 耗时（秒）


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    session_id: str
    agent_metadata: AgentMetadata | None = None  # 新增：agent 元数据


class DemoInfo(BaseModel):
    """Demo 信息模型"""
    id: str
    name: str
    description: str
    category: str
    coming_soon: bool = False


class DemosResponse(BaseModel):
    """Demo 列表响应模型"""
    demos: list[DemoInfo]


# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info(f"🚀 {config.APP_NAME} v{config.APP_VERSION} 启动中...")
    logger.info("=" * 60)

    # 启动时初始化
    logger.info("✅ FastAPI 服务器已启动")
    logger.info(f"📝 环境: {'开发' if config.DEBUG else '生产'}")
    logger.info(f"🔑 LangSmith 追踪: {'启用' if config.LANGSMITH_TRACING else '禁用'}")

    yield

    # 关闭时清理
    logger.info("🛑 FastAPI 服务器正在关闭...")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Multi-Agent 系统聊天接口",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 健康检查 ====================

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.APP_VERSION
    }


# ==================== Demo 管理 ====================

@app.get("/api/demos", response_model=DemosResponse, tags=["Demo"])
async def list_demos():
    """获取可用的 Demo 列表"""
    return {
        "demos": [
            {
                "id": "deepagents",
                "name": "Multi-Agent System",
                "description": "基于 Deep Agents 的协作式 AI 系统：Orchestrator 协调 Coder 和 SRE 专家",
                "category": "Agents"
            },
            {
                "id": "basic-chat",
                "name": "基础 LLM 问答",
                "description": "最简单的对话功能，验证前后端联通",
                "category": "基础"
            },
            {
                "id": "document-chat",
                "name": "文档问答（RAG）",
                "description": "上传文档后进行问答，基于检索增强生成",
                "category": "RAG",
                "coming_soon": True
            }
        ]
    }


# ==================== 聊天接口 ====================

@app.post("/api/chat", response_model=ChatResponse, tags=["聊天"])
async def chat(request: ChatRequest):
    """
    非流式聊天接口

    Args:
        request: 聊天请求，包含 message、session_id 和 demo_id

    Returns:
        ChatResponse: 包含响应文本、会话 ID 和 agent 元数据（仅 deepagents）
    """
    try:
        logger.info(f"📨 收到聊天请求: demo={request.demo_id}, session={request.session_id}, message={request.message[:50]}...")

        # 根据 demo_id 路由到不同的处理函数
        if request.demo_id == "basic-chat":
            # Basic Chat Demo
            response_text = await basic_chat.chat_response(
                user_input=request.message,
                session_id=request.session_id
            )
            return ChatResponse(
                response=response_text,
                session_id=request.session_id,
                agent_metadata=None  # basic-chat 没有 agent 元数据
            )

        elif request.demo_id == "deepagents":
            # DeepAgents Demo（包含 agent 元数据）
            result = await deepagents_demo.chat_response_with_metadata(
                user_input=request.message,
                session_id=request.session_id
            )

            # 提取 tracker_summary 并转换为 agent_metadata
            tracker_summary = result.get("tracker_summary", {})

            # 提取 skill 名称列表
            skill_calls_data = tracker_summary.get("skill_calls", [])
            skill_names = [call.get("skill_name", "") for call in skill_calls_data if call.get("skill_name")]

            agent_metadata = AgentMetadata(
                agent_type=result.get("agent"),  # orchestrator, coder, sre
                delegations=tracker_summary.get("delegation_count", 0),
                tool_calls=tracker_summary.get("tool_call_count", 0),
                skill_calls=tracker_summary.get("skill_call_count", 0),
                skills=skill_names,
                duration=tracker_summary.get("duration", 0.0)
            )

            logger.info(f"✅ 聊天响应完成: session={request.session_id}, agent={agent_metadata.agent_type}, length={len(result['response'])}")

            return ChatResponse(
                response=result["response"],
                session_id=request.session_id,
                agent_metadata=agent_metadata
            )

        else:
            # 未知的 demo_id
            raise HTTPException(
                status_code=400,
                detail=f"未知的 demo_id: {request.demo_id}. 可用选项: basic-chat, deepagents"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream", tags=["聊天"])
async def chat_stream_endpoint(request: ChatRequest):
    """
    流式聊天接口

    Args:
        request: 聊天请求，包含 message、session_id 和 demo_id

    Returns:
        StreamingResponse: 流式响应
    """
    async def generate():
        """生成流式响应"""
        try:
            logger.info(f"📨 收到流式聊天请求: demo={request.demo_id}, session={request.session_id}")

            # 根据 demo_id 路由到不同的处理函数
            if request.demo_id == "basic-chat":
                # Basic Chat Demo
                async for chunk in basic_chat.chat_stream(
                    user_input=request.message,
                    session_id=request.session_id
                ):
                    yield chunk

            elif request.demo_id == "deepagents":
                # DeepAgents Demo（流式 + 元数据）
                async for chunk in deepagents_demo.chat_stream_with_metadata(
                    user_input=request.message,
                    session_id=request.session_id
                ):
                    yield chunk

            else:
                # 未知的 demo_id
                yield f"错误: 未知的 demo_id: {request.demo_id}. 可用选项: basic-chat, deepagents"
                return

            logger.info(f"✅ 流式聊天响应完成: session={request.session_id}")

        except Exception as e:
            logger.error(f"❌ 流式聊天处理失败: {e}")
            yield f"\n[错误: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/chat/clear", tags=["聊天"])
async def clear_chat_history(request: ChatRequest):
    """
    清空对话历史

    清空指定会话的对话历史。

    Args:
        request: 包含 session_id 和 demo_id 的请求

    Returns:
        确认消息
    """
    try:
        logger.info(f"🗑️ 收到清空历史请求: demo={request.demo_id}, session={request.session_id}")

        # 根据 demo_id 路由到不同的处理函数
        if request.demo_id == "basic-chat":
            # Basic Chat Demo
            basic_chat.clear_history(request.session_id)
        elif request.demo_id == "deepagents":
            # DeepAgents Demo
            await deepagents_demo.clear_history(request.session_id)
        else:
            # 未知的 demo_id
            raise HTTPException(
                status_code=400,
                detail=f"未知的 demo_id: {request.demo_id}. 可用选项: basic-chat, deepagents"
            )

        return {
            "status": "success",
            "message": "对话历史已清空",
            "session_id": request.session_id,
            "demo_id": request.demo_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 清空历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/history", tags=["聊天"])
async def get_chat_history(
    session_id: str,
    demo_id: str = "deepagents"
):
    """
    获取指定会话的历史消息记录

    Args:
        session_id: 会话 ID
        demo_id: Demo ID（默认 deepagents）

    Returns:
        历史消息列表，前端 Message 格式
    """
    from langchain_core.messages import HumanMessage, AIMessage
    from agents import get_orchestrator_with_checkpointer
    from common.session_manager import get_session_manager

    try:
        logger.info(f"📜 收到历史请求: demo={demo_id}, session={session_id}")

        # Basic Chat 使用内存存储，无法获取历史
        if demo_id == "basic-chat":
            return []

        # DeepAgents 从 checkpoint 读取历史
        elif demo_id == "deepagents":
            session_manager = get_session_manager()
            config = await session_manager.get_config(session_id, demo_id)

            # 直接使用 checkpointer 获取历史
            checkpointer = await session_manager._ensure_checkpointer()
            checkpoint_tuple = await checkpointer.aget_tuple(config)

            if not checkpoint_tuple:
                logger.info(f"📭 无历史记录: session={session_id}")
                return []

            # 提取消息历史
            messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])

            # 转换为前端格式
            history = []
            for i, msg in enumerate(messages):
                # 处理字典格式的消息（LangChain .dict() 格式）
                if isinstance(msg, dict):
                    msg_type = msg.get("type", "")

                    # LangChain 格式: type="human" -> user
                    if msg_type == "human":
                        content = msg.get("content", "")
                        if content:
                            history.append({
                                "id": f"history-{i}",
                                "role": "user",
                                "content": content,
                                "timestamp": 0
                            })

                    # LangChain 格式: type="ai" -> assistant
                    elif msg_type == "ai":
                        content = msg.get("content", "")
                        # 跳过空内容的 AI 消息（纯工具调用）
                        if content and content.strip():
                            history.append({
                                "id": f"history-{i}",
                                "role": "assistant",
                                "content": content,
                                "timestamp": 0
                            })

                    # LangChain 格式: type="tool" -> assistant (子代理的完整回答)
                    elif msg_type == "tool":
                        content = msg.get("content", "")
                        if content and content.strip():
                            history.append({
                                "id": f"history-{i}",
                                "role": "assistant",
                                "content": content,
                                "timestamp": 0
                            })

                # 处理 LangChain BaseMessage 对象
                else:
                    msg_type = type(msg).__name__

                    # HumanMessage -> user
                    if isinstance(msg, HumanMessage):
                        content = msg.content if hasattr(msg, 'content') else str(msg)
                        if content:  # 跳过空内容
                            history.append({
                                "id": f"history-{i}",
                                "role": "user",
                                "content": content,
                                "timestamp": 0
                            })

                    # AIMessage -> assistant（跳过 tool 消息）
                    elif isinstance(msg, AIMessage):
                        # 跳过纯工具调用消息（没有实际内容）
                        content = msg.content if hasattr(msg, 'content') else ""
                        if not content or content.strip() == "":
                            continue

                        history.append({
                            "id": f"history-{i}",
                            "role": "assistant",
                            "content": content,
                            "timestamp": 0
                        })

            logger.info(f"✅ 获取历史成功: {len(history)} 条消息")
            return history

        else:
            raise HTTPException(
                status_code=400,
                detail=f"未知的 demo_id: {demo_id}. 可用选项: basic-chat, deepagents"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 启动服务器 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=config.DEBUG,
        log_level="info"
    )
