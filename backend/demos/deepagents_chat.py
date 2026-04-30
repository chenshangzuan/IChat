"""
Demo 2: DeepAgents Multi-Agent System

使用 LangChain Deep Agents 实现 multi-agent 协作系统。
主 Orchestrator 协调 Coder 和 SRE 两个专家子代理。
"""
from typing import AsyncIterator, Dict, Any
import re
import logging
import sys
import asyncio
import json

from common.langfuse import langfuse_handler
from common.sse import sse_content, sse_event

from agents import get_orchestrator_with_store
from common.agent_tracker import AgentTracker
from common.agent_registry import detect_agent_type as detect_agent
from common.session_manager import get_session_manager

# 配置日志 - 确保在终端中可见
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)


def extract_tool_calls_detail(messages: list) -> list[dict]:
    """
    从消息历史中提取工具调用详情

    Args:
        messages: 消息历史列表

    Returns:
        工具调用详情列表，每个包含 tool_name, output, status
    """
    tool_details = []
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'tool':
            tool_name = getattr(msg, 'name', 'unknown_tool')
            content = msg.content if hasattr(msg, 'content') else ""
            # 截断过长的输出
            if len(content) > 1000:
                content = content[:1000] + "...(已截断)"
            tool_details.append({
                "tool_name": tool_name,
                "output": content,
                "status": "completed"
            })
    return tool_details



async def chat_response(user_input: str, session_id: str = "default", user_id: str = "") -> Dict[str, Any]:
    """
    非流式聊天响应（包含元数据和审批支持）

    Returns:
        正常完成:
        {
            "interrupted": False,
            "response": str,
            "agent_type": str,
            "delegations": int,
            "tool_calls": int,
            "duration": float,
            "tool_calls_detail": list[dict],
            # 兼容字段
            "agent": str,
            "all_messages": list,
            "tracker_summary": dict,
        }
        审批中断:
        {
            "interrupted": True,
            "actions": list[dict],  # [{name, args, description}]
            "timestamp": str,
            "response": "",
            "agent": "",
            "tool_calls_detail": [],
            "delegations": 0,
            "tool_calls": 0,
            "duration": float,
        }
    """
    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    tracker = AgentTracker(session_id)
    tracker.log_session_start(user_input)

    logger.info(f"🔵 收到请求: session={session_id}, input={user_input[:80]}")

    config = await session_manager.get_config(session_id, "deepagents")

    from agents.deepagents import AgentContext
    from langgraph.errors import GraphInterrupt

    interrupted = False
    interrupt_actions = []

    try:
        result = await orchestrator.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            context=AgentContext(user_id=user_id),
        )
    except GraphInterrupt:
        interrupted = True
        try:
            state = await orchestrator.aget_state(config)
            for task in state.tasks:
                for intr in getattr(task, 'interrupts', []):
                    value = intr.value if hasattr(intr, 'value') else intr
                    if isinstance(value, dict):
                        for action_req in value.get("action_requests", []):
                            interrupt_actions.append({
                                "name": action_req.get("name", ""),
                                "args": action_req.get("args", {}),
                                "description": action_req.get("description", ""),
                            })
        except Exception as e:
            logger.warning(f"  ⚠️ 读取 interrupt 详情失败: {e}")
        logger.info(f"  🛑 检测到 interrupt，共 {len(interrupt_actions)} 个待审批操作")

    if interrupted:
        tracker.log_session_complete()
        from datetime import datetime, timezone
        return {
            "interrupted": True,
            "actions": interrupt_actions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response": "",
            "agent": "",
            "tool_calls_detail": [],
            "delegations": 0,
            "tool_calls": 0,
            "duration": tracker.get_summary().get("duration", 0.0),
        }

    # 从 checkpoint 读取当前轮完整消息
    turn_messages = result["messages"]
    try:
        state = await orchestrator.aget_state(config)
        checkpoint_msgs = state.values.get("messages", [])
        if checkpoint_msgs:
            last_human_idx = -1
            for i, msg in enumerate(checkpoint_msgs):
                msg_type = getattr(msg, 'type', '') or (msg.get('type', '') if isinstance(msg, dict) else '')
                if msg_type == 'human':
                    last_human_idx = i
            if last_human_idx >= 0:
                turn_messages = checkpoint_msgs[last_human_idx + 1:]
    except Exception as e:
        logger.warning(f"  ⚠️ 读取 checkpoint 消息失败，使用 ainvoke 结果: {e}")

    tracker.detect_and_log_tool_calls(turn_messages)

    response = turn_messages[-1].content if turn_messages else ""
    for msg in reversed(turn_messages):
        msg_type = getattr(msg, 'type', '') or (msg.get('type', '') if isinstance(msg, dict) else '')
        if msg_type == 'ai':
            content = msg.content if hasattr(msg, 'content') else msg.get('content', '') if isinstance(msg, dict) else ''
            if content and content.strip():
                response = content
                break

    tracker.log_session_complete()
    tracker_summary = tracker.get_summary()
    tool_calls_detail = extract_tool_calls_detail(turn_messages)
    detected_agent = detect_agent(response)

    logger.info(f"🟢 完成: agent={detected_agent}, tools={tracker_summary.get('tool_call_count', 0)}, duration={tracker_summary.get('duration', 0):.1f}s")

    return {
        "interrupted": False,
        "response": response,
        "agent_type": detected_agent,
        "delegations": tracker_summary.get("delegation_count", 0),
        "tool_calls": tracker_summary.get("tool_call_count", 0),
        "duration": tracker_summary.get("duration", 0.0),
        "tool_calls_detail": tool_calls_detail,
        "agent": detected_agent,
        "all_messages": turn_messages,
        "tracker_summary": tracker_summary,
    }


async def chat_stream(user_input: str, session_id: str = "default") -> AsyncIterator[str]:
    """
    流式聊天响应

    Args:
        user_input: 用户输入
        session_id: 会话 ID（用于多轮对话）

    Yields:
        Agent 的响应文本片段
    """
    # 获取会话管理器和 orchestrator
    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    # 获取会话配置（包含 thread_id）
    config = await session_manager.get_config(session_id, "deepagents")

    async for chunk in orchestrator.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
        stream_mode="messages"
    ):
        # 提取内容块
        if hasattr(chunk, 'content'):
            yield sse_content(chunk.content)


async def _process_stream(orchestrator, astream_input, config, user_id: str, session_id: str, tracker: AgentTracker) -> AsyncIterator[str]:
    """
    公共流式处理逻辑（chat_stream_with_metadata 和 chat_approve_stream 共用）

    使用单模式 stream_mode="messages"：
    - messages 模式：处理 AI/tool 消息

    注意：updates 模式会导致 astream 永远不完成，因此不使用。

    Yields:
        流式文本片段、事件标记、元数据标记
    """
    from agents.deepagents import AgentContext
    from datetime import datetime, timezone

    all_messages = []
    interrupted = False

    async for chunk in orchestrator.astream(
        astream_input,
        config=config,
        context=AgentContext(user_id=user_id),
        stream_mode=["messages", "updates"]
    ):
        # 双模式下chunk是(mode, payload)元组
        if not isinstance(chunk, tuple) or len(chunk) < 2:
            logger.warning(f"  ⚠️ chunk格式不符预期: type={type(chunk).__name__}")
            continue

        mode, payload = chunk[0], chunk[1]

        if mode == "messages":
            # payload是(message, metadata)元组
            if isinstance(payload, tuple) and len(payload) >= 1:
                message = payload[0]
            else:
                message = payload

            all_messages.append(message)

            # 检查消息类型（兼容AIMessage/AIMessageChunk和ToolMessage/ToolMessageChunk）
            msg_type = getattr(message, 'type', 'unknown')
            msg_class = message.__class__.__name__
            is_ai_message = msg_type == 'ai' or 'ai' in msg_class.lower()
            is_tool_message = msg_type == 'tool' or 'tool' in msg_class.lower()

            if is_ai_message:
                # 记录 tool_calls
                tool_calls = getattr(message, 'tool_calls', None)
                if tool_calls:
                    for tc in tool_calls:
                        tc_name = tc.get('name', '') if isinstance(tc, dict) else getattr(tc, 'name', '')
                        tc_args = tc.get('args', {}) if isinstance(tc, dict) else getattr(tc, 'args', {})
                        logger.info(f"  🤖 模型调用工具: {tc_name}({json.dumps(tc_args, ensure_ascii=False)[:200]})")

                # 发送文本内容
                content = getattr(message, 'content', '')
                if content:
                    yield sse_content(content)

            elif is_tool_message:
                # 发送工具调用事件
                tool_name = getattr(message, 'name', 'unknown_tool')
                tool_content = message.content if hasattr(message, 'content') else ""
                logger.info(f"  🔧 工具结果: {tool_name} → {tool_content[:200]}")
                if len(tool_content) > 1000:
                    tool_content = tool_content[:1000] + "...(已截断)"
                tool_event = json.dumps({
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "output": tool_content,
                    "status": "completed"
                }, ensure_ascii=False)
                yield sse_event("tool_call", tool_event)

        elif mode == "updates":
            # 处理interrupt事件（审批请求）
            from datetime import datetime, timezone

            if isinstance(payload, dict) and "__interrupt__" in payload:
                interrupts = payload["__interrupt__"]
                logger.info(f"  🛑 检测到 interrupt，共 {len(interrupts)} 个待审批操作")

                # 提取action信息
                actions = []
                for intr in interrupts:
                    value = intr.value if hasattr(intr, 'value') else intr
                    if isinstance(value, dict):
                        for action_req in value.get("action_requests", []):
                            actions.append({
                                "name": action_req.get("name", ""),
                                "args": action_req.get("args", {}),
                                "description": action_req.get("description", ""),
                            })

                # 发送审批事件
                interrupted = True
                approval_event = json.dumps({
                    "type": "approval_request",
                    "actions": actions,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }, ensure_ascii=False)
                yield sse_event("approval", approval_event)
                logger.info(f"  📋 审批事件: {[a['name'] for a in actions]}")

    if not interrupted:
        # 正常完成（无 interrupt），发送元数据
        # 从 checkpoint 读取当前轮完整消息（从最后一条 HumanMessage 起），
        # 避免审批恢复后只统计到 resume 阶段的消息
        turn_messages = all_messages
        try:
            state = await orchestrator.aget_state(config)
            checkpoint_msgs = state.values.get("messages", [])
            if checkpoint_msgs:
                # 找到最后一条 HumanMessage 的位置，取其后的所有消息
                last_human_idx = -1
                for i, msg in enumerate(checkpoint_msgs):
                    msg_type = getattr(msg, 'type', '') or (msg.get('type', '') if isinstance(msg, dict) else '')
                    if msg_type == 'human':
                        last_human_idx = i
                if last_human_idx >= 0:
                    turn_messages = checkpoint_msgs[last_human_idx + 1:]
        except Exception as e:
            logger.warning(f"  ⚠️ 读取 checkpoint 消息失败，使用流消息: {e}")

        tracker.detect_and_log_tool_calls(turn_messages)

        response_content = ""
        for msg in reversed(turn_messages):
            msg_type = getattr(msg, 'type', '') or (msg.get('type', '') if isinstance(msg, dict) else '')
            if msg_type == 'ai':
                content = msg.content if hasattr(msg, 'content') else msg.get('content', '') if isinstance(msg, dict) else ''
                if content and content.strip():
                    response_content = content
                    break

        detected_agent = detect_agent(response_content)
        tracker.log_session_complete()

        tracker_summary = tracker.get_summary()
        tool_calls_detail = extract_tool_calls_detail(turn_messages)

        metadata = {
            "agent_type": detected_agent,
            "delegations": tracker_summary.get("delegation_count", 0),
            "tool_calls": tracker_summary.get("tool_call_count", 0),
            "duration": tracker_summary.get("duration", 0.0),
            "tool_calls_detail": tool_calls_detail,
        }

        logger.info(f"🟢 完成: agent={detected_agent}, tools={metadata.get('tool_calls', 0)}, duration={metadata.get('duration', 0):.1f}s")

        yield sse_event("metadata", json.dumps(metadata))
    else:
        logger.info("⏸️ 流暂停，等待用户审批")


async def chat_stream_with_metadata(user_input: str, session_id: str = "default", user_id: str = "") -> AsyncIterator[str]:
    """
    流式聊天响应（包含元数据和审批支持）
    """
    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    tracker = AgentTracker(session_id)
    tracker.log_session_start(user_input)

    logger.info(f"🔵 收到请求: session={session_id}, input={user_input[:80]}")

    config = await session_manager.get_config(session_id, "deepagents")
    astream_input = {"messages": [{"role": "user", "content": user_input}]}

    async for chunk in _process_stream(orchestrator, astream_input, config, user_id, session_id, tracker):
        yield chunk


async def chat_approve_stream(
    session_id: str = "default",
    user_id: str = "",
    decisions: list = None,
) -> AsyncIterator[str]:
    """
    审批恢复流式响应
    """
    from langgraph.types import Command

    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    tracker = AgentTracker(session_id)
    tracker.log_session_start("[approval-resume]")

    logger.info(f"🔵 审批恢复: session={session_id}, decisions={decisions}")

    config = await session_manager.get_config(session_id, "deepagents")

    hitl_decisions = []
    for d in (decisions or []):
        if d.get("type") == "approve":
            hitl_decisions.append({"type": "approve"})
        elif d.get("type") == "reject":
            hitl_decisions.append({
                "type": "reject",
                "message": d.get("message", "用户拒绝了此操作"),
            })

    resume_value = {"decisions": hitl_decisions}
    astream_input = Command(resume=resume_value)

    async for chunk in _process_stream(orchestrator, astream_input, config, user_id, session_id, tracker):
        yield chunk


async def clear_history(session_id: str = "default"):
    """
    清空对话历史

    通过删除 checkpoint 来清空指定会话的对话历史。

    Args:
        session_id: 会话 ID
    """
    session_manager = get_session_manager()
    await session_manager.clear_session(session_id, "deepagents")
