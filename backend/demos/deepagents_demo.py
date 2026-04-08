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

from agents import get_orchestrator_with_store
from agents.skill_tracking_middleware import (
    clear_skill_calls_context,
)
from common.agent_tracker import AgentTracker
from common.session_manager import get_session_manager

# 配置日志 - 确保在终端中可见
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)


def detect_agent(response: str) -> str:
    """
    从响应中检测是哪个 agent 在回复

    与 AgentTracker._detect_agent_type() 保持一致的逻辑

    Args:
        response: Agent 响应文本

    Returns:
        Agent 类型: "orchestrator", "coder", "sre"
        默认返回 "orchestrator"（因为这是主代理）
    """
    import re

    response_lower = response.lower()

    # 先检测 Orchestrator 的特征（更优先，避免误判）
    # 如果包含这些介绍性关键词，很可能是 Orchestrator 在介绍系统
    orchestrator_indicators = [
        r"orchestrator\s*agent",
        r"协调以下专家",
        r"协调.*专家.*agent",
        r"我会.*委托",
        r"请告诉我.*需要",
    ]

    for indicator in orchestrator_indicators:
        if re.search(indicator, response_lower):
            return "orchestrator"

    # 检测子代理的签名响应 - 必须在开头且是签名格式
    # Coder Agent 签名：必须在开头，且有冒号，后面不是" - "（列表格式）
    coder_sig_pattern = r"^[\s\S]{0,60}👨‍💻\s*\*\*\s*coder[ -]agent\s*\*\*\s*:(?!.*\s-\s)"
    if re.search(coder_sig_pattern, response_lower):
        return "coder"

    # SRE Agent 签名
    sre_sig_pattern = r"^[\s\S]{0,60}🔧\s*\*\*\s*sre[ -]agent\s*\*\*\s*:(?!.*\s-\s)"
    if re.search(sre_sig_pattern, response_lower):
        return "sre"

    # 检查是否是 Orchestrator 的汇总（包含 "Agent 完成"）
    if re.search(r"agent\s+完成|完成\s*任务", response_lower):
        return "orchestrator"

    # 默认返回 orchestrator
    return "orchestrator"


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


async def chat_response(user_input: str, session_id: str = "default") -> str:
    """
    非流式聊天响应

    Args:
        user_input: 用户输入
        session_id: 会话 ID（用于多轮对话）

    Returns:
        Agent 的响应文本
    """
    # 获取会话管理器和 orchestrator
    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    # 创建跟踪器
    tracker = AgentTracker(session_id)
    tracker.log_session_start(user_input)

    logger.info("=" * 60)
    logger.info(f"🔵 [DeepAgents Demo] 收到请求")
    logger.info(f"  Session ID: {session_id}")
    logger.info(f"  用户输入: {user_input[:100]}...")
    logger.info("=" * 60)

    # 获取会话配置（包含 thread_id）
    config = await session_manager.get_config(session_id, "deepagents")

    result = await orchestrator.ainvoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config
    )

    # 使用跟踪器分析消息历史
    tracker.detect_and_log_tool_calls(result["messages"])

    # 打印消息历史
    logger.info(f"📋 [DeepAgents Demo] 消息历史长度: {len(result['messages'])}")
    for i, msg in enumerate(result["messages"]):
        msg_type = getattr(msg, 'type', 'unknown')
        msg_content = msg.content if hasattr(msg, 'content') else str(msg)[:100]

        # 检查是否有工具调用
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                # 处理 tool_call 可能是字典或对象的情况
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})
                    if isinstance(tool_args, dict):
                        args_str = str(tool_args)[:100]
                    else:
                        args_str = str(tool_args)[:100]
                else:
                    tool_name = tool_call.name if hasattr(tool_call, 'name') else 'unknown'
                    tool_args = tool_call.args if hasattr(tool_call, 'args') else {}
                    args_str = str(tool_args)[:100] if tool_args else '{}'

                logger.info(f"  [{i}] {msg_type} → 工具调用: {tool_name}({args_str})")
        else:
            logger.info(f"  [{i}] {msg_type}: {msg_content}...")

    # 找到来自子代理的完整响应
    # DeepAgents 的消息结构:
    # - [0] human - 用户输入
    # - [1] ai - Orchestrator 响应（简短）
    # - [2] tool - 子代理的完整响应（包含代码/详细内容）
    # - [3] ai - 最后的摘要
    response = result["messages"][-1].content  # 默认返回最后一条消息
    for msg in result["messages"]:
        msg_type = getattr(msg, 'type', '')
        # 优先返回 tool 类型的消息（子代理的完整响应）
        if msg_type == 'tool' and hasattr(msg, 'content'):
            response = msg.content
            break

    detected_agent = detect_agent(response)

    logger.info("=" * 60)
    logger.info(f"🟢 [DeepAgents Demo] 响应完成")
    logger.info(f"  检测到的 Agent: {detected_agent}")
    logger.info(f"  响应长度: {len(response)} 字符")
    logger.info("=" * 60)

    tracker.log_session_complete()

    return response


async def chat_response_with_metadata(user_input: str, session_id: str = "default", user_id: str = "") -> Dict[str, Any]:
    """
    非流式聊天响应（包含元数据）

    Args:
        user_input: 用户输入
        session_id: 会话 ID（用于多轮对话）

    Returns:
        包含响应和元数据的字典:
        {
            "response": str,           # 响应文本
            "agent": str,              # 响应的 agent 类型
            "all_messages": list,      # 所有消息历史
            "tracker_summary": dict,   # 跟踪器摘要（委托事件、工具调用等）
        }
    """
    # 获取会话管理器和 orchestrator
    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    # 创建跟踪器
    tracker = AgentTracker(session_id)
    tracker.log_session_start(user_input)

    # 获取会话配置（包含 thread_id）
    config = await session_manager.get_config(session_id, "deepagents")

    from agents.deepagents import AgentContext
    result = await orchestrator.ainvoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
        context=AgentContext(user_id=user_id),
    )

    # 使用跟踪器分析消息历史
    tracker.detect_and_log_tool_calls(result["messages"])

    # 找到来自子代理的完整响应（与 chat_response 相同的逻辑）
    response = result["messages"][-1].content  # 默认返回最后一条消息

    # 调试：打印所有消息类型
    logger.info(f"📋 [DEBUG] 总消息数: {len(result['messages'])}")
    for i, msg in enumerate(result["messages"]):
        msg_type = getattr(msg, 'type', '')
        msg_class = type(msg).__name__
        content_len = len(msg.content) if hasattr(msg, 'content') else 0
        logger.info(f"📋 [DEBUG] [{i}] {msg_class} (type={msg_type}, {content_len} 字符)")

    for msg in result["messages"]:
        msg_type = getattr(msg, 'type', '')
        # 优先返回 tool 类型的消息（子代理的完整响应）
        if msg_type == 'tool' and hasattr(msg, 'content'):
            response = msg.content
            logger.info(f"✅ [DEBUG] 找到 tool 消息，长度: {len(response)}")
            break

    agent = detect_agent(response)

    tracker.log_session_complete()

    return {
        "response": response,
        "agent": agent,
        "all_messages": result["messages"],
        "tracker_summary": tracker.get_summary(),
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
            yield chunk.content


async def chat_stream_with_metadata(user_input: str, session_id: str = "default", user_id: str = "") -> AsyncIterator[str]:
    """
    流式聊天响应（包含元数据）

    流结束时发送特殊的元数据标记，格式为：
    \n__METADATA__:json字符串

    Args:
        user_input: 用户输入
        session_id: 会话 ID（用于多轮对话）

    Yields:
        Agent 的响应文本片段
    """
    # 获取会话管理器和 orchestrator
    session_manager = get_session_manager()
    orchestrator = await get_orchestrator_with_store()

    # 清空上下文变量，为新的请求准备
    clear_skill_calls_context()

    # 创建跟踪器
    tracker = AgentTracker(session_id)
    tracker.log_session_start(user_input)

    logger.info("=" * 60)
    logger.info(f"🔵 [DeepAgents Demo] 收到流式请求")
    logger.info(f"  Session ID: {session_id}")
    logger.info(f"  用户输入: {user_input[:100]}...")
    logger.info("=" * 60)

    # 收集所有消息用于元数据分析
    all_messages = []

    # 获取会话配置（包含 thread_id）
    config = await session_manager.get_config(session_id, "deepagents")

    from agents.deepagents import AgentContext
    # 流式输出响应
    async for chunk in orchestrator.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
        context=AgentContext(user_id=user_id),
        stream_mode="messages"
    ):
        # deepagents 的 astream 返回 tuple: (AIMessage, metadata)
        if isinstance(chunk, tuple) and len(chunk) >= 1:
            message = chunk[0]  # AIMessage
            # 收集消息用于分析
            all_messages.append(message)

            # print("流式消息:", message)
            # 获取消息类型
            msg_type = getattr(message, 'type', 'unknown')
            logger.debug(f"  流式消息类型: {msg_type}")

            if msg_type == 'ai' and hasattr(message, 'content') and message.content:
                # AI 消息：发送文本事件
                content = message.content
                # 每 50 个字符为一个块，模拟打字效果
                for i in range(0, len(content), 50):
                    yield content[i:i+50]
                    await asyncio.sleep(0.02)
            elif msg_type == 'tool':
                # 工具消息：发送独立的工具事件（单独一行，便于前端解析）
                tool_name = getattr(message, 'name', 'unknown_tool')
                tool_content = message.content if hasattr(message, 'content') else ""
                # 截断过长的输出
                if len(tool_content) > 1000:
                    tool_content = tool_content[:1000] + "...(已截断)"
                # 发送工具事件（单独一行，使用 __EVENT__ 前缀）
                tool_event = json.dumps({
                    "type": "tool_call",
                    "tool_name": tool_name,
                    "output": tool_content,
                    "status": "completed"
                }, ensure_ascii=False)
                yield f"\n__EVENT__:{tool_event}\n"
                logger.info(f"  📦 发送工具事件: {tool_name}")
        elif hasattr(chunk, 'content') and chunk.content:
            # 兼容其他可能的格式（作为 AI 消息处理）
            all_messages.append(chunk)
            content = chunk.content
            for i in range(0, len(content), 50):
                yield content[i:i+50]
                await asyncio.sleep(0.02)

    # 使用跟踪器分析消息历史
    tracker.detect_and_log_tool_calls(all_messages)

    # 找到响应文本（优先使用 ai 类型消息，排除 tool 类型）
    response_content = ""
    # 反向遍历，找到最后一条 ai 类型的消息
    for msg in reversed(all_messages):
        msg_type = getattr(msg, 'type', '')
        if msg_type == 'ai' and hasattr(msg, 'content') and msg.content:
            response_content = msg.content
            break
    # 如果没有找到 ai 消息，使用最后一条非 tool 消息
    if not response_content and all_messages:
        for msg in reversed(all_messages):
            msg_type = getattr(msg, 'type', '')
            if msg_type != 'tool' and hasattr(msg, 'content') and msg.content:
                response_content = msg.content
                break

    # 检测 agent 类型
    detected_agent = detect_agent(response_content)

    tracker.log_session_complete()

    # 获取跟踪器摘要
    tracker_summary = tracker.get_summary()

    # 提取 skill 名称列表
    skill_calls_data = tracker_summary.get("skill_calls", [])
    skill_names = [call.get("skill_name", "") for call in skill_calls_data if call.get("skill_name")]

    # 提取工具调用详情
    tool_calls_detail = extract_tool_calls_detail(all_messages)

    # 构建元数据
    metadata = {
        "agent_type": detected_agent,
        "delegations": tracker_summary.get("delegation_count", 0),
        "tool_calls": tracker_summary.get("tool_call_count", 0),
        "skill_calls": tracker_summary.get("skill_call_count", 0),
        "skills": skill_names,
        "duration": tracker_summary.get("duration", 0.0),
        "tool_calls_detail": tool_calls_detail  # 新增：工具调用详情
    }

    logger.info("=" * 60)
    logger.info(f"🟢 [DeepAgents Demo] 流式响应完成")
    logger.info(f"  检测到的 Agent: {detected_agent}")
    logger.info(f"  元数据: {metadata}")
    logger.info("=" * 60)

    # 发送元数据标记（特殊格式，前端解析）
    yield f"\n__METADATA__:{json.dumps(metadata)}"


async def clear_history(session_id: str = "default"):
    """
    清空对话历史

    通过删除 checkpoint 来清空指定会话的对话历史。

    Args:
        session_id: 会话 ID
    """
    session_manager = get_session_manager()
    await session_manager.clear_session(session_id, "deepagents")
