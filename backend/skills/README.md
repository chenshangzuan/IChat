# Skills 目录说明

这个目录包含子代理（subagents）的技能定义。每个技能都是一个独立的文件夹，包含 `SKILL.md` 文件描述该技能的能力和使用方式。

## 目录结构

```
skills/
├── coder/                          # Coder Agent 的技能
│   ├── code_review/               # 代码审查技能
│   │   └── SKILL.md
│   ├── code_generation/           # 代码生成技能
│   │   └── SKILL.md
│   └── code_optimization/         # 代码优化技能
│       └── SKILL.md
│
└── sre/                            # SRE Agent 的技能
    ├── log_analysis/              # 日志分析技能
    │   └── SKILL.md
    ├── deployment/                # 部署技能
    │   └── SKILL.md
    ├── sql_audit/                 # SQL 审核技能
    │   └── SKILL.md
    └── audit_log_normalization/   # 审计日志规范化技能
        ├── SKILL.md               # 必须，主文件
        ├── references/            # 可选，参考文档
        │   ├── rule.md            # 规则文档
        │   └── example.md         # 示例文档
        ├── scripts/               # 可选，可执行脚本
        └── assets/                # 可选，模板、图标等资源
```

## 标准技能结构

每个技能文件夹遵循以下标准结构：

```
your-skill-name/
├── SKILL.md          # 必须，主文件
├── scripts/          # 可选，可执行脚本
├── references/       # 可选，参考文档
└── assets/           # 可选，模板、图标等资源
```

### SKILL.md（必须）

技能的主文件，使用以下格式：

```markdown
---
name: skill-name
description: Brief description of when to use this skill.
---

# Skill Name

## Overview
[Brief description of what this skill does]

## Capabilities
- **Capability 1**: Description
- **Capability 2**: Description

## Instructions
[Step-by-step instructions for using this skill]

## Output Format
```markdown
# Output Format Title
[Template for the response]
```

## When to Use
Use this skill when:
- User asks for X
- User mentions Y
- [Other triggers]
```

### scripts/（可选）

存放可执行脚本，例如：
- Python 脚本（`.py`）
- Shell 脚本（`.sh`）
- JavaScript 脚本（`.js`）

### references/（可选）

存放参考文档，例如：
- `rule.md` - 规则说明
- `example.md` - 示例文档
- `api.md` - API 文档
- 其他参考资料

### assets/（可选）

存放资源文件，例如：
- 模板文件
- 图标/图片
- 配置文件示例

## 如何添加新技能

### 步骤 1: 创建技能文件夹

在对应的 agent 目录下创建新的技能文件夹：

```bash
# 为 coder 添加新技能
mkdir -p skills/coder/debugging

# 为 sre 添加新技能
mkdir -p skills/sre/monitoring
```

### 步骤 2: 创建 SKILL.md 文件

在技能文件夹中创建 `SKILL.md` 文件，使用上面的标准格式。

### 步骤 3: 添加可选子目录（根据需要）

```bash
# 如果技能有参考文档
mkdir -p skills/sre/your-skill/references

# 如果技能有可执行脚本
mkdir -p skills/sre/your-skill/scripts

# 如果技能有资源文件
mkdir -p skills/sre/your-skill/assets
```

### 步骤 4: 重启服务

```bash
# 重启后端服务
uv run uvicorn main:app --reload --port 8000
```

## 技能文件夹命名规范

- 使用小写字母和下划线：`sql_audit`、`log_analysis`
- 简洁描述性名称：`code_review` 而不是 `CodeReview`
- 使用英文文件夹名：`sql_audit` 而不是 `SQL审核`

## 技能自动加载

Skills 目录中的所有 `SKILL.md` 文件会被 Deep Agents 框架自动加载。

**DeepAgents 支持完整的技能目录结构**：
- `SKILL.md` - 主文件（必须），包含技能定义和使用说明
- `scripts/` - 可执行脚本（可选），框架可以调用这些脚本
- `references/` - 参考文档（可选），Agent 可以引用这些文档
- `assets/` - 资源文件（可选），包含模板、图标等

**重要**：不需要修改代码引用，DeepAgents 会自动发现并加载所有技能。

## 当前可用的技能

### Coder Agent (`skills/coder/`)

| 技能 | 名称 | 描述 |
|------|------|------|
| `code_review/` | 代码审查 | 审查代码质量，发现潜在问题，提供改进建议 |
| `code_generation/` | 代码生成 | 根据功能描述生成高质量、可维护的代码 |
| `code_optimization/` | 代码优化 | 优化现有代码的性能、可读性或结构 |

### SRE Agent (`skills/sre/`)

| 技能 | 名称 | 描述 |
|------|------|------|
| `log_analysis/` | 日志分析 | 分析系统和应用日志，发现问题和模式 |
| `deployment/` | 部署管理 | 执行和管理服务部署流程 |
| `sql_audit/` | SQL 审核 | 审核 SQL 查询的性能和安全性 |
| `audit_log_normalization/` | 审计日志规范化 | 将接口行为描述转换为标准格式 [Action] [Service] [Resource] |

## 注意事项

1. **文件格式**: 必须是 Markdown (`.md`) 文件
2. **Frontmatter**: 必须包含 `name` 和 `description` 字段
3. **文件夹结构**: 每个技能必须有独立的文件夹
4. **文件名**: 技能描述文件必须命名为 `SKILL.md`（大写）
5. **重启服务**: 添加新技能后需要重启后端服务
