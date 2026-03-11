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
            agent_metadata = AgentMetadata(
                agent_type=result.get("agent"),  # orchestrator, coder, sre
                delegations=tracker_summary.get("delegation_count", 0),
                tool_calls=tracker_summary.get("tool_call_count", 0),
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
                # DeepAgents Demo
                async for chunk in deepagents_demo.chat_stream(
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

    注意：当前版本暂不支持历史记录清理。
    需要集成 LangGraph checkpointer 后才能实现。

    Args:
        request: 包含 session_id 的请求

    Returns:
        确认消息
    """
    # TODO: 集成 LangGraph checkpointer 后实现
    return {
        "status": "not_implemented",
        "message": "历史记录清理功能暂未实现，需要集成 LangGraph checkpointer",
        "session_id": request.session_id
    }


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
