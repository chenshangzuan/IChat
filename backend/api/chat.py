import logging
import traceback

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import (
    AgentMetadata,
    ApprovalRequest,
    ChatRequest,
    ChatResponse,
    EditMessageRequest,
)
from common.sse import sse_event
from demos import basic_chat, deepagents_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"📨 收到聊天请求: demo={request.demo_id}, session={request.session_id}, message={request.message[:50]}...")

        if request.demo_id == "basic-chat":
            response_text = await basic_chat.chat_response(
                user_input=request.message,
                session_id=request.session_id,
            )
            return ChatResponse(response=response_text, session_id=request.session_id)

        elif request.demo_id == "deepagents":
            result = await deepagents_chat.chat_response(
                user_input=request.message,
                session_id=request.session_id,
                user_id=request.user_id,
            )
            tracker_summary = result.get("tracker_summary", {})
            agent_metadata = AgentMetadata(
                agent_type=result.get("agent"),
                delegations=tracker_summary.get("delegation_count", 0),
                tool_calls=tracker_summary.get("tool_call_count", 0),
                duration=tracker_summary.get("duration", 0.0),
            )
            logger.info(f"✅ 聊天响应完成: session={request.session_id}, agent={agent_metadata.agent_type}, length={len(result['response'])}")
            return ChatResponse(
                response=result["response"],
                session_id=request.session_id,
                agent_metadata=agent_metadata,
            )

        else:
            raise HTTPException(status_code=400, detail=f"未知的 demo_id: {request.demo_id}. 可用选项: basic-chat, deepagents")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        try:
            logger.info(f"📨 收到流式聊天请求: demo={request.demo_id}, session={request.session_id}")

            if request.demo_id == "basic-chat":
                async for chunk in basic_chat.chat_stream(
                    user_input=request.message,
                    session_id=request.session_id,
                ):
                    yield chunk

            elif request.demo_id == "deepagents":
                async for chunk in deepagents_chat.chat_stream_with_metadata(
                    user_input=request.message,
                    session_id=request.session_id,
                    user_id=request.user_id,
                ):
                    yield chunk

            else:
                yield sse_event("error", f"未知的 demo_id: {request.demo_id}. 可用选项: basic-chat, deepagents")
                return

            logger.info(f"✅ 流式聊天响应完成: session={request.session_id}")

        except Exception as e:
            logger.error(f"❌ 流式聊天处理失败: {e}")
            yield sse_event("error", str(e))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/approve")
async def chat_approve(request: ApprovalRequest):
    async def generate():
        try:
            logger.info(f"📨 收到审批请求: session={request.session_id}, decisions={[d.type for d in request.decisions]}")
            decisions = [{"type": d.type, "message": d.message} for d in request.decisions]
            async for chunk in deepagents_chat.chat_approve_stream(
                session_id=request.session_id,
                user_id=request.user_id,
                decisions=decisions,
            ):
                yield chunk
            logger.info(f"✅ 审批恢复响应完成: session={request.session_id}")

        except Exception as e:
            logger.error(f"❌ 审批恢复处理失败: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            yield sse_event("error", str(e))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/clear")
async def clear_chat_history(request: ChatRequest):
    try:
        logger.info(f"🗑️ 收到清空历史请求: demo={request.demo_id}, session={request.session_id}")

        if request.demo_id == "basic-chat":
            basic_chat.clear_history(request.session_id)
        elif request.demo_id == "deepagents":
            await deepagents_chat.clear_history(request.session_id)
        else:
            raise HTTPException(status_code=400, detail=f"未知的 demo_id: {request.demo_id}. 可用选项: basic-chat, deepagents")

        return {"status": "success", "message": "对话历史已清空", "session_id": request.session_id, "demo_id": request.demo_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 清空历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit")
async def edit_message(request: EditMessageRequest):
    from agents import get_orchestrator_with_store
    from common.session_manager import get_session_manager
    from langchain_core.messages import RemoveMessage

    try:
        logger.info(f"✏️ 编辑消息: session={request.session_id}, index={request.message_index}")

        session_manager = get_session_manager()
        config = await session_manager.get_config(request.session_id, request.demo_id)

        orchestrator = await get_orchestrator_with_store()
        state = await orchestrator.aget_state(config)

        messages = state.values.get("messages", [])
        if request.message_index < 0 or request.message_index >= len(messages):
            raise HTTPException(status_code=400, detail=f"无效的消息索引: {request.message_index}")

        messages_to_remove = messages[request.message_index:]
        remove_ops = [RemoveMessage(id=msg.id) for msg in messages_to_remove if hasattr(msg, "id") and msg.id]
        await orchestrator.aupdate_state(config, {"messages": remove_ops})

        logger.info(f"✅ 消息已截断: {len(messages)} → {len(messages) - len(remove_ops)}, 删除 {len(remove_ops)} 条")
        return {"status": "success", "original_count": len(messages), "truncated_count": len(messages) - len(remove_ops)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 编辑消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_chat_history(session_id: str, demo_id: str = "deepagents"):
    from datetime import datetime, timezone

    from agents import get_orchestrator_with_checkpointer, get_orchestrator_with_store
    from common.session_manager import get_session_manager
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    try:
        logger.info(f"📜 收到历史请求: demo={demo_id}, session={session_id}")

        if demo_id == "basic-chat":
            return []

        elif demo_id == "deepagents":
            session_manager = get_session_manager()
            config = await session_manager.get_config(session_id, demo_id)

            checkpointer = await session_manager._ensure_checkpointer()
            checkpoint_tuple = await checkpointer.aget_tuple(config)

            if not checkpoint_tuple:
                logger.info(f"📭 无历史记录: session={session_id}")
                return []

            messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
            history = []

            for i, msg in enumerate(messages):
                if isinstance(msg, dict):
                    msg_type = msg.get("type", "")
                    if msg_type == "human":
                        content = msg.get("content", "")
                        if content:
                            history.append({"id": f"history-{i}", "role": "user", "content": content, "timestamp": 0})
                    elif msg_type == "ai":
                        content = msg.get("content", "")
                        if content and content.strip():
                            history.append({"id": f"history-{i}", "role": "assistant", "content": content, "timestamp": 0})
                    elif msg_type == "tool":
                        content = msg.get("content", "")
                        tool_name = msg.get("name", "unknown_tool")
                        if content and content.strip():
                            history.append({
                                "id": f"history-{i}",
                                "role": "tool",
                                "content": content,
                                "timestamp": 0,
                                "toolInfo": {"toolName": tool_name, "status": "completed"},
                            })
                else:
                    if isinstance(msg, HumanMessage):
                        content = msg.content if hasattr(msg, "content") else str(msg)
                        if content:
                            history.append({"id": f"history-{i}", "role": "user", "content": content, "timestamp": 0})
                    elif isinstance(msg, AIMessage):
                        content = msg.content if hasattr(msg, "content") else ""
                        if not content or content.strip() == "":
                            continue
                        history.append({"id": f"history-{i}", "role": "assistant", "content": content, "timestamp": 0})
                    elif isinstance(msg, ToolMessage):
                        content = msg.content if hasattr(msg, "content") else ""
                        tool_name = msg.name if hasattr(msg, "name") else "unknown_tool"
                        if content and content.strip():
                            history.append({
                                "id": f"history-{i}",
                                "role": "tool",
                                "content": content,
                                "timestamp": 0,
                                "toolInfo": {"toolName": tool_name, "status": "completed"},
                            })

            # 恢复待审批的 interrupt
            orchestrator = await get_orchestrator_with_store()
            state = await orchestrator.aget_state(config)
            if state.next and state.interrupts:
                for intr in state.interrupts:
                    value = intr.value if hasattr(intr, "value") else intr
                    if isinstance(value, dict):
                        actions = [
                            {"name": ar.get("name", ""), "args": ar.get("args", {}), "description": ar.get("description", "")}
                            for ar in value.get("action_requests", [])
                        ]
                        if actions:
                            history.append({
                                "id": f"approval-{len(history)}",
                                "role": "approval",
                                "content": "",
                                "timestamp": 0,
                                "approvalInfo": {
                                    "actions": actions,
                                    "status": "pending",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                            })
                logger.info(f"📋 恢复待审批消息: {len(state.interrupts)} 个")

            logger.info(f"✅ 获取历史成功: {len(history)} 条消息")
            return history

        else:
            raise HTTPException(status_code=400, detail=f"未知的 demo_id: {demo_id}. 可用选项: basic-chat, deepagents")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_chat_sessions(demo_id: str = "deepagents"):
    from common.session_manager import get_session_manager

    try:
        session_manager = get_session_manager()
        checkpointer = await session_manager._ensure_checkpointer()

        prefix = f"{demo_id}:"
        async with checkpointer.lock:
            cursor = await checkpointer.conn.execute(
                "SELECT DISTINCT thread_id FROM checkpoints WHERE thread_id LIKE ? ORDER BY thread_id DESC",
                (f"{prefix}%",),
            )
            rows = await cursor.fetchall()

        sessions = []
        for (thread_id,) in rows:
            session_id = thread_id[len(prefix):]
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = await checkpointer.aget_tuple(config)
            if not checkpoint_tuple:
                continue

            messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
            title = ""
            for msg in messages:
                msg_type = getattr(msg, "type", "") or (msg.get("type", "") if isinstance(msg, dict) else "")
                if msg_type == "human":
                    content = msg.content if hasattr(msg, "content") else msg.get("content", "")
                    if content:
                        title = content[:30].strip()
                        if len(content) > 30:
                            title += "..."
                        break

            if not title:
                continue

            timestamp = 0
            try:
                ts_str = session_id.replace("session-", "")
                timestamp = int(ts_str)
            except (ValueError, IndexError):
                pass

            sessions.append({
                "session_id": session_id,
                "title": title,
                "timestamp": timestamp,
                "message_count": len(messages),
            })

        sessions.sort(key=lambda s: s["timestamp"], reverse=True)
        logger.info(f"📋 获取会话列表: demo={demo_id}, count={len(sessions)}")
        return sessions

    except Exception as e:
        logger.error(f"❌ 获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, demo_id: str = "deepagents"):
    try:
        logger.info(f"🗑️ 收到删除会话请求: demo={demo_id}, session={session_id}")

        if demo_id == "basic-chat":
            basic_chat.clear_history(session_id)
        elif demo_id == "deepagents":
            await deepagents_chat.clear_history(session_id)
        else:
            raise HTTPException(status_code=400, detail=f"未知的 demo_id: {demo_id}. 可用选项: basic-chat, deepagents")

        return {"status": "success", "message": "会话已删除", "session_id": session_id, "demo_id": demo_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
