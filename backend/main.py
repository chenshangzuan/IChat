"""
IChat FastAPI 服务器
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config import config
from api import system, demos, chat, wechat_work

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f"🚀 {config.APP_NAME} v{config.APP_VERSION} 启动中...")
    logger.info("=" * 60)
    logger.info("✅ FastAPI 服务器已启动")
    logger.info(f"📝 环境: {'开发' if config.DEBUG else '生产'}")
    logger.info(f"🔑 LangSmith 追踪: {'启用' if config.LANGSMITH_TRACING else '禁用'}")
    logger.info(f"🔑 Langfuse 追踪: {'启用' if config.LANGFUSE_TRACING else '禁用'}")
    yield
    logger.info("🛑 FastAPI 服务器正在关闭...")


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="Multi-Agent 系统聊天接口",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(demos.router)
app.include_router(chat.router)
app.include_router(wechat_work.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=config.DEBUG, log_level="info")
