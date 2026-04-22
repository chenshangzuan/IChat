from fastapi import APIRouter

from api.schemas import DemosResponse

router = APIRouter(prefix="/api/demos", tags=["Demo"])


@router.get("", response_model=DemosResponse)
async def list_demos():
    return {
        "demos": [
            {
                "id": "deepagents",
                "name": "Multi-Agent System",
                "description": "基于 Deep Agents 的协作式 AI 系统：Orchestrator 协调 Coder 和 SRE 专家",
                "category": "Agents",
            },
            {
                "id": "basic-chat",
                "name": "基础 LLM 问答",
                "description": "最简单的对话功能，验证前后端联通",
                "category": "基础",
            },
            {
                "id": "document-chat",
                "name": "文档问答（RAG）",
                "description": "上传文档后进行问答，基于检索增强生成",
                "category": "RAG",
                "coming_soon": True,
            },
        ]
    }
