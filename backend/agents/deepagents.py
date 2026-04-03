"""
Deep Agents Multi-Agent 系统配置

使用 LangChain Deep Agents 的 create_deep_agent 创建 multi-agent 系统。
每个子代理通过 skills 参数指向技能目录。
"""
from deepagents import create_deep_agent
from models import default_llm
import logging
import sys

# 配置日志 - 确保在终端中可见
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout,  # 明确输出到标准输出
    force=True  # 强制重新配置（即使已经配置过）
)
logger = logging.getLogger(__name__)


def _build_coder_prompt() -> str:
    """构建 Coder Agent 的系统提示词（动态加载 skills）"""
    from agents.skill_loader import get_coder_skills, format_skills_list
    skills_info = format_skills_list(get_coder_skills())

    return f"""你是代码专家。

## 技能
{skills_info}

## 规则
- 禁止使用任何工具，直接在响应中提供代码
- 响应以 "👨‍💻 **Coder Agent**: [任务摘要]" 开头
- 代码使用 markdown 代码块格式
- 提供完整、可运行的代码
"""


# 定义 Coder 子代理
coder_subagent = {
    "name": "coder-agent",
    "description": "Expert coder for writing, reviewing, and optimizing code. Use this agent for any code-related tasks.",
    "model": default_llm,
    "tools": [],
    "skills": ["skills/coder/"],
    "system_prompt": _build_coder_prompt(),
}


def _build_sre_prompt() -> str:
    """构建 SRE Agent 的系统提示词（动态加载 skills）"""
    from agents.skill_loader import get_sre_skills, format_skills_list
    skills_info = format_skills_list(get_sre_skills())

    return f"""你是运维专家。

## 技能
{skills_info}

## 服务名称映射（必须遵守）
| 输入 | 正确输出 |
|---|---|
| ecs, ECS, EC2, VM, Server, 云服务器 | **ZEC** |
| rds, RDS, Database, MySQL, PostgreSQL | **DB** |
| oss, OSS, S3, Storage, 对象存储 | **BMC** |
| vpc, VPC, Network, 网络 | **Network** |
| iam, IAM, Identity, Permission, 权限 | **IAM** |

## 动词映射（必须遵守）
| 非标准 | 正确标准 |
|---|---|
| Query, Search, Find | **List** 或 **Describe** |
| Fetch, Retrieve, Show, View | **Get** 或 **Describe** |
| Read | **Get** |

格式：`[Action] [Service] [Resource]`，如 `List ZEC Instance`、`Get BMC Bucket`

## 规则
- 禁止使用任何工具，直接在响应中提供答案
- 响应以 "🔧 **SRE Agent**: [任务摘要]" 开头
"""


# 定义 SRE 子代理
sre_subagent = {
    "name": "sre-agent",
    "description": "Expert SRE for deployment, log analysis, SQL auditing, and infrastructure tasks. Use this agent for operations-related work.",
    "model": default_llm,
    "tools": [],
    "skills": ["skills/sre/"],
    "system_prompt": _build_sre_prompt(),
}


# 创建主 Orchestrator Agent
def create_orchestrator(checkpointer=None, store=None):
    """
    创建主协调器 Agent，管理 Coder 和 SRE 子代理

    Args:
        checkpointer: LangGraph checkpointer 实例（用于会话记忆）
        store: LangGraph store 实例（用于长期记忆）
    """

    logger.info("=" * 60)
    logger.info("🚀 [Agents] 正在创建 Orchestrator Agent...")
    if checkpointer:
        logger.info(f"📝 [Agents] 已启用 checkpointer: {type(checkpointer).__name__}")
    if store:
        logger.info(f"📦 [Agents] 已启用 store: {type(store).__name__}")

    # 动态加载 skills 信息
    from agents.skill_loader import get_coder_skills, get_sre_skills, format_skills_list
    coder_skills = get_coder_skills()
    sre_skills = get_sre_skills()
    coder_skills_info = format_skills_list(coder_skills)
    sre_skills_info = format_skills_list(sre_skills)

    system_prompt = f"""你是协调者，管理 Coder 和 SRE 两个专家代理。

## 直接回答（不委托）
- 问候语（你好、hi）
- 能力询问（你有哪些 skills、你会什么）
- 简单问题（1+1=?、通用知识）

## 委托规则

**委托给 coder-agent**（关键词：写、编写、创建、代码、实现、开发、算法、编程语言名）
**委托给 sre-agent**（关键词：日志、部署、SQL、数据库、Nginx、服务器、运维、审计、规范化）

## 可用专家

### 👨‍💻 Coder Agent
{coder_skills_info}

### 🔧 SRE Agent
{sre_skills_info}

## 响应格式
- 直接回答：友好回复
- 委托后：总结结果，如 "👨‍💻 **Coder Agent 完成**: [摘要]"

记住：你是协调者，不是执行者。正确委托是你的价值所在！
"""

    logger.info(f"🤖 [Agents] 配置的子代理:")
    logger.info(f"  - {coder_subagent['name']}: {coder_subagent['description'][:50]}...")
    logger.info(f"  - {sre_subagent['name']}: {sre_subagent['description'][:50]}...")

    # 导入 backend 工厂
    from agents.backend_factory import make_backend

    # 创建 agent，支持长期记忆和混合存储后端
    agent = create_deep_agent(
        model=default_llm,
        subagents=[coder_subagent, sre_subagent],
        system_prompt=system_prompt,
        debug=False,
        checkpointer=checkpointer,      # 会话记忆支持
        store=store,                    # 长期记忆支持
        backend=make_backend,           # 混合存储后端
    )

    # 打印 agent 的图信息
    if hasattr(agent, 'graph'):
        logger.info(f"📊 [Agents] 图节点: {list(agent.graph.nodes.keys())}")

    logger.info(f"✅ [Agents] Orchestrator Agent 创建完成!")
    logger.info("=" * 60)

    return agent


async def create_orchestrator_with_store(checkpointer=None):
    """
    创建带长期记忆的 Orchestrator Agent

    支持 Checkpoint（会话状态）和 Store（长期记忆）的混合存储策略。

    Args:
        checkpointer: LangGraph checkpointer 实例（可选）

    Returns:
        配置了 store 和 backend 的 orchestrator agent
    """
    from common.store_manager import get_store_manager

    store_manager = get_store_manager()
    store = await store_manager.get_store()

    return create_orchestrator(
        checkpointer=checkpointer,
        store=store
    )


# 全局实例
logger.info("🔧 [Agents] 正在初始化全局 orchestrator 实例...")
orchestrator = create_orchestrator()
