"""
Agent Tracker - 跟踪多代理系统的委托过程

记录：
- 代理间的委托事件
- 工具调用详情
- 代理响应状态
- 时间戳和性能指标
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from langchain_core.messages import BaseMessage

# 配置日志 - 确保在终端中可见
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)

logger = logging.getLogger(__name__)


@dataclass
class DelegationEvent:
    """代理委托事件"""
    from_agent: str  # 源代理
    to_agent: str  # 目标代理
    task_description: str  # 任务描述
    tool_name: str  # 工具名称
    tool_args: Dict[str, Any]  # 工具参数
    timestamp: str  # 时间戳

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCallEvent:
    """工具调用事件"""
    tool_name: str
    args: Dict[str, Any]
    agent_name: str
    status: str  # initiated, completed, failed
    timestamp: str
    result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResponse:
    """代理响应"""
    agent_name: str
    agent_type: str  # orchestrator, coder, sre
    content: str
    timestamp: str
    message_index: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkillCallEvent:
    """Skill 调用事件"""
    skill_name: str  # skill 名称，如 "code-review", "audit-log-normalization"
    agent_name: str  # 调用该 skill 的 agent
    agent_type: str  # agent 类型: coder, sre
    task_summary: str  # 任务摘要
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AgentTracker:
    """
    代理跟踪器

    跟踪 multi-agent 系统中的所有委托事件、理响应。工具调用和代
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.delegations: List[DelegationEvent] = []
        self.tool_calls: List[ToolCallEvent] = []
        self.responses: List[AgentResponse] = []
        self.skill_calls: List[SkillCallEvent] = []  # 新增：skill 调用记录
        self.start_time = datetime.now()

        logger.info("=" * 80)
        logger.info(f"🔍 [AgentTracker] 会话 {session_id} 跟踪器已初始化")
        logger.info("=" * 80)

    def log_delegation(
        self,
        from_agent: str,
        to_agent: str,
        task_description: str,
        tool_name: str,
        tool_args: Dict[str, Any]
    ):
        """记录代理委托事件"""
        event = DelegationEvent(
            from_agent=from_agent,
            to_agent=to_agent,
            task_description=task_description,
            tool_name=tool_name,
            tool_args=tool_args,
            timestamp=datetime.now().isoformat()
        )
        self.delegations.append(event)

        # 输出漂亮的委托日志
        logger.info("")
        logger.info("🔄 " + "=" * 76)
        logger.info(f"🔄 [AgentTracker] 📢 代理委托事件")
        logger.info("🔄 " + "=" * 76)
        logger.info(f"🔄 [AgentTracker] 📤 从: {self._format_agent_name(from_agent)}")
        logger.info(f"🔄 [AgentTracker] 📥 到: {self._format_agent_name(to_agent)}")
        logger.info(f"🔄 [AgentTracker] 🔧 工具: {tool_name}")
        logger.info(f"🔄 [AgentTracker] 📋 任务: {task_description[:100]}...")
        logger.info("🔄 " + "=" * 76)
        logger.info("")

    def log_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        agent_name: str,
        status: str = "initiated",
        result: Optional[str] = None
    ):
        """记录工具调用事件"""
        event = ToolCallEvent(
            tool_name=tool_name,
            args=args,
            agent_name=agent_name,
            status=status,
            timestamp=datetime.now().isoformat(),
            result=result
        )
        self.tool_calls.append(event)

        if status == "initiated":
            logger.info(f"⚙️  [AgentTracker] 🔨 工具调用启动: {tool_name}")
            logger.info(f"⚙️  [AgentTracker] 👤 执行者: {agent_name}")
            if args:
                logger.info(f"⚙️  [AgentTracker] 📦 参数: {json.dumps(args, ensure_ascii=False)[:200]}...")
        elif status == "completed":
            logger.info(f"✅ [AgentTracker] ✨ 工具调用完成: {tool_name}")
            if result:
                logger.info(f"✅ [AgentTracker] 📄 结果预览: {result[:100]}...")
        elif status == "failed":
            logger.error(f"❌ [AgentTracker] 💥 工具调用失败: {tool_name}")

    def log_agent_response(
        self,
        agent_name: str,
        agent_type: str,
        content: str,
        message_index: int
    ):
        """记录代理响应"""
        event = AgentResponse(
            agent_name=agent_name,
            agent_type=agent_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            message_index=message_index
        )
        self.responses.append(event)

        # 输出响应日志
        icon = self._get_agent_icon(agent_type)
        logger.info("")
        logger.info(f"{icon} [AgentTracker] 💬 {agent_name} 响应")
        logger.info(f"{icon} [AgentTracker] 📊 消息索引: {message_index}")
        logger.info(f"{icon} [AgentTracker] 📝 内容长度: {len(content)} 字符")
        logger.info("")

    def log_skill_call(
        self,
        skill_name: str,
        agent_name: str,
        agent_type: str,
        task_summary: str
    ):
        """记录 skill 调用事件"""
        event = SkillCallEvent(
            skill_name=skill_name,
            agent_name=agent_name,
            agent_type=agent_type,
            task_summary=task_summary,
            timestamp=datetime.now().isoformat()
        )
        self.skill_calls.append(event)

        # 输出 skill 调用日志
        icon = self._get_skill_icon(skill_name)
        logger.info("")
        logger.info(f"{icon} [AgentTracker] 🎨 Skill 调用")
        logger.info(f"{icon} [AgentTracker] 📦 Skill: {skill_name}")
        logger.info(f"{icon} [AgentTracker] 👤 Agent: {agent_name} ({agent_type})")
        logger.info(f"{icon} [AgentTracker] 📋 任务: {task_summary[:100]}...")
        logger.info("")

    def log_session_start(self, user_input: str):
        """记录会话开始"""
        logger.info("")
        logger.info("🚀 " + "=" * 76)
        logger.info(f"🚀 [AgentTracker] 🎯 新会话开始")
        logger.info("🚀 " + "=" * 76)
        logger.info(f"🚀 [AgentTracker] 👤 用户输入: {user_input[:150]}...")
        logger.info(f"🚀 [AgentTracker] 🆔 会话 ID: {self.session_id}")
        logger.info("🚀 " + "=" * 76)
        logger.info("")

    def log_session_complete(self):
        """记录会话完成"""
        duration = (datetime.now() - self.start_time).total_seconds()

        logger.info("")
        logger.info("🎊 " + "=" * 76)
        logger.info(f"🎊 [AgentTracker] 🏁 会话完成")
        logger.info("🎊 " + "=" * 76)
        logger.info(f"🎊 [AgentTracker] ⏱️  总耗时: {duration:.2f} 秒")
        logger.info(f"🎊 [AgentTracker] 🔄 委托次数: {len(self.delegations)}")
        logger.info(f"🎊 [AgentTracker] ⚙️  工具调用: {len(self.tool_calls)}")
        logger.info(f"🎊 [AgentTracker] 🎨 Skill 调用: {len(self.skill_calls)}")
        logger.info(f"🎊 [AgentTracker] 💬 响应数量: {len(self.responses)}")
        logger.info("🎊 " + "=" * 76)
        logger.info("")

    def get_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "session_id": self.session_id,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "delegation_count": len(self.delegations),
            "tool_call_count": len(self.tool_calls),
            "skill_call_count": len(self.skill_calls),  # 新增
            "response_count": len(self.responses),
            "delegations": [d.to_dict() for d in self.delegations],
            "tool_calls": [t.to_dict() for t in self.tool_calls],
            "skill_calls": [s.to_dict() for s in self.skill_calls],  # 新增
            "responses": [r.to_dict() for r in self.responses],
        }

    def detect_and_log_tool_calls(self, messages: List[BaseMessage]):
        """检测并记录消息历史中的工具调用"""
        for i, msg in enumerate(messages):
            # 检查是否有工具调用
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # 处理 tool_call 可能是字典或对象的情况
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get('name', 'unknown')
                        args = tool_call.get('args', {}) if isinstance(tool_call.get('args'), dict) else {}
                    else:
                        tool_name = tool_call.name if hasattr(tool_call, 'name') else 'unknown'
                        args = tool_call.args if isinstance(tool_call.args, dict) else {}

                    # 确定调用者
                    caller = "unknown"
                    if i > 0:
                        prev_msg = messages[i - 1]
                        if hasattr(prev_msg, 'type'):
                            caller = prev_msg.type

                    # 记录工具调用
                    self.log_tool_call(
                        tool_name=tool_name,
                        args=args,
                        agent_name=caller,
                        status="initiated"
                    )

                    # 检测是否是 agent 委托（task 工具调用）
                    if tool_name == "task" or tool_name == "Task":
                        # 从参数中提取委托信息
                        subagent_type = args.get('subagent_type', 'unknown')
                        description = args.get('description', '')

                        # 映射 subagent_type 到可读名称
                        subagent_names = {
                            'coder-agent': 'Coder Agent',
                            'sre-agent': 'SRE Agent',
                            'general-purpose': 'General Agent'
                        }

                        # 记录委托事件
                        self.log_delegation(
                            from_agent=caller,
                            to_agent=subagent_names.get(subagent_type, subagent_type),
                            task_description=description,
                            tool_name=tool_name,
                            tool_args=args
                        )

            # 记录代理响应
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                agent_type = self._detect_agent_type(msg.content)
                agent_name = self._get_agent_name_from_type(agent_type)

                self.log_agent_response(
                    agent_name=agent_name,
                    agent_type=agent_type,
                    content=msg.content,
                    message_index=i
                )

                # 如果是子代理（coder 或 sre），检测并记录使用的 skill
                if agent_type in ["coder", "sre"]:
                    skill_name = self._detect_skill_from_content(msg.content, agent_type)
                    if skill_name:
                        # 生成任务摘要（取前100个字符）
                        task_summary = msg.content[:100]
                        self.log_skill_call(
                            skill_name=skill_name,
                            agent_name=agent_name,
                            agent_type=agent_type,
                            task_summary=task_summary
                        )

    def _format_agent_name(self, name: str) -> str:
        """格式化代理名称"""
        agent_icons = {
            "orchestrator": "🎯 Orchestrator",
            "coder-agent": "👨‍💻 Coder Agent",
            "sre-agent": "🔧 SRE Agent",
            "general-purpose": "🛠️ General Agent",
        }
        return agent_icons.get(name, name)

    def _get_agent_icon(self, agent_type: str) -> str:
        """获取代理图标"""
        icons = {
            "orchestrator": "🎯",
            "coder": "👨‍💻",
            "sre": "🔧",
            "unknown": "🤖",
        }
        return icons.get(agent_type, "🤖")

    def _detect_agent_type(self, content: str) -> str:
        """从内容中检测代理类型

        关键区分：
        - 子代理签名：在开头，格式 "emoji **Agent Name**: 内容"（冒号后紧跟内容）
        - Orchestrator 介绍：提到子代理但不是签名，如列表格式 "1. **emoji Agent Name** - 描述"
        """
        import re

        content_lower = content.lower()

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
            if re.search(indicator, content_lower):
                return "orchestrator"

        # 检测子代理的签名响应 - 必须在开头且是签名格式
        # 子代理签名格式：开头60字符内，emoji + **Agent Name**: 后面直接跟内容
        # 关键：冒号后要么换行，要么紧跟内容（不是列表格式）

        # Coder Agent 签名：必须在开头，且有冒号，后面不是" - "（列表格式）
        coder_sig_pattern = r"^[\s\S]{0,60}👨‍💻\s*\*\*\s*coder[ -]agent\s*\*\*\s*:(?!.*\s-\s)"
        if re.search(coder_sig_pattern, content_lower):
            return "coder"

        # SRE Agent 签名
        sre_sig_pattern = r"^[\s\S]{0,60}🔧\s*\*\*\s*sre[ -]agent\s*\*\*\s*:(?!.*\s-\s)"
        if re.search(sre_sig_pattern, content_lower):
            return "sre"

        # 检查是否是 Orchestrator 的汇总（包含 "Agent 完成"）
        if re.search(r"agent\s+完成|完成\s*任务", content_lower):
            return "orchestrator"

        # 默认返回 orchestrator
        return "orchestrator"

    def _get_agent_name_from_type(self, agent_type: str) -> str:
        """从代理类型获取名称"""
        names = {
            "orchestrator": "Orchestrator",
            "coder": "Coder Agent",
            "sre": "SRE Agent",
            "unknown": "Unknown Agent",
        }
        return names.get(agent_type, "Unknown")

    def _get_skill_icon(self, skill_name: str) -> str:
        """获取 skill 图标"""
        icons = {
            # Coder skills
            "code-generation": "✨",
            "code-optimization": "⚡",
            "code-review": "🔍",
            # SRE skills
            "log-analysis": "📊",
            "deployment": "🚀",
            "sql-audit": "🗄️",
            "audit-log-normalization": "📋",
            "sre-operations": "🔧",
        }
        return icons.get(skill_name, "🎨")

    def _detect_skill_from_content(self, content: str, agent_type: str) -> str:
        """从内容中检测使用的 skill

        Args:
            content: 子代理的响应内容
            agent_type: agent 类型 (coder, sre)

        Returns:
            检测到的 skill 名称，如果未检测到返回空字符串
        """
        import re

        content_lower = content.lower()

        # 定义每个 agent 的 skill 检测模式
        skill_patterns = {
            "coder": {
                "code-generation": [
                    r"create.*implementation",
                    r"write.*code",
                    r"implement",
                    r"生成.*代码",
                    r"编写.*实现",
                ],
                "code-optimization": [
                    r"optimi[sz]e",
                    r"refactor",
                    r"improve.*performance",
                    r"优化",
                    r"重构",
                ],
                "code-review": [
                    r"review",
                    r"audit.*code",
                    r"代码审查",
                    r"代码审核",
                ],
            },
            "sre": {
                "log-analysis": [
                    r"log.*analy[sz]is",
                    r"analy[sz]e.*log",
                    r"日志.*分析",
                    r"分析.*日志",
                ],
                "deployment": [
                    r"deplo[y]",
                    r"release",
                    r"部署",
                    r"发布",
                ],
                "sql-audit": [
                    r"sql.*audit",
                    r"query.*review",
                    r"sql.*优化",
                    r"sql.*审核",
                ],
                "audit-log-normalization": [
                    r"audit.*log.*normali[zs]ation",
                    r"normali[zs]e.*audit",
                    r"接口.*规范",
                    r"接口.*标准化",
                    r"audit.*log",
                ],
                "sre-operations": [
                    r"operation",
                    r"infrastructure",
                    r"运维",
                ],
            },
        }

        # 获取当前 agent 的 skill 模式
        agent_skills = skill_patterns.get(agent_type, {})

        # 检测匹配的 skill
        for skill_name, patterns in agent_skills.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return skill_name

        return ""  # 未检测到具体 skill
