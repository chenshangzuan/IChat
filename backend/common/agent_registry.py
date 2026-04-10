"""
Agent Registry - 集中式 Agent 元数据管理

所有 agent 的 name、type、icon、display_name 在此定义一次，
其他模块通过 lookup 函数按不同 key 查询。
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgentInfo:
    """单个 Agent 的元数据"""
    agent_type: str        # 规范类型: "orchestrator", "coder", "sre"
    subagent_name: str     # 子代理名: "coder-agent", "sre-agent"
    display_name: str      # 显示名: "Coder Agent"
    icon: str              # emoji: "👨‍💻"
    skill_dir: Optional[str]  # skills 目录名: "coder", "sre", None


# ── 主注册表 ─────────────────────────────────────────────────
AGENTS: list[AgentInfo] = [
    AgentInfo(
        agent_type="orchestrator",
        subagent_name="orchestrator",
        display_name="Orchestrator",
        icon="🎯",
        skill_dir=None,
    ),
    AgentInfo(
        agent_type="coder",
        subagent_name="coder-agent",
        display_name="Coder Agent",
        icon="👨‍💻",
        skill_dir="coder",
    ),
    AgentInfo(
        agent_type="sre",
        subagent_name="sre-agent",
        display_name="SRE Agent",
        icon="🔧",
        skill_dir="sre",
    ),
    AgentInfo(
        agent_type="general",
        subagent_name="general-purpose",
        display_name="General Agent",
        icon="🛠️",
        skill_dir=None,
    ),
]

_UNKNOWN = AgentInfo(
    agent_type="unknown",
    subagent_name="unknown",
    display_name="Unknown Agent",
    icon="🤖",
    skill_dir=None,
)

# ── Lookup dicts（import 时构建一次）────────────────────────
_by_type: dict[str, AgentInfo] = {a.agent_type: a for a in AGENTS}
_by_subagent_name: dict[str, AgentInfo] = {a.subagent_name: a for a in AGENTS}
_by_skill_dir: dict[str, AgentInfo] = {
    a.skill_dir: a for a in AGENTS if a.skill_dir
}


def get_by_type(agent_type: str) -> AgentInfo:
    return _by_type.get(agent_type, _UNKNOWN)


def get_by_subagent_name(name: str) -> AgentInfo:
    return _by_subagent_name.get(name, _UNKNOWN)


def get_by_skill_dir(dir_name: str) -> AgentInfo:
    return _by_skill_dir.get(dir_name, _UNKNOWN)


def format_agent_name(name: str) -> str:
    """'coder-agent' -> '👨‍💻 Coder Agent'（日志用）"""
    info = _by_subagent_name.get(name)
    if info is None:
        return name
    return f"{info.icon} {info.display_name}"


# ── Agent 类型检测（唯一实现）────────────────────────────────
def detect_agent_type(content: str) -> str:
    """从响应内容检测 agent 类型

    关键区分：
    - 子代理签名：在开头，格式 "emoji **Agent Name**: 内容"（冒号后紧跟内容）
    - Orchestrator 介绍：提到子代理但不是签名，如列表格式 "1. **emoji Agent Name** - 描述"
    """
    content_lower = content.lower()

    # 先检测 Orchestrator 的特征（更优先，避免误判）
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

    # 检测子代理的签名响应 - 用 AGENTS 动态生成正则
    for agent in AGENTS:
        if agent.agent_type in ("orchestrator", "general", "unknown"):
            continue
        escaped_icon = re.escape(agent.icon)
        name_pattern = agent.subagent_name.replace("-", "[ -]")
        sig_pattern = (
            rf"^[\s\S]{{0,60}}{escaped_icon}\s*\*\*\s*"
            rf"{name_pattern}\s*\*\*\s*:(?!.*\s-\s)"
        )
        if re.search(sig_pattern, content_lower):
            return agent.agent_type

    # Orchestrator 汇总
    if re.search(r"agent\s+完成|完成\s*任务", content_lower):
        return "orchestrator"

    return "orchestrator"
