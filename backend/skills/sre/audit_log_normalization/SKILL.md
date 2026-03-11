---
name: audit-log-normalization
description: Use this skill for normalizing audit logs and standardizing interface behavior descriptions to [Action] [Service] [Resource] format.
---

# Audit Log Normalization Skill

## Overview

This skill converts interface behavior descriptions or operation codes into standardized format following event naming specification: **`[Action] [Service] [Resource]`**

## Capabilities

- **Format Normalization**: Convert snake_case, kebab-case, CamelCase to standard Title Case
- **Action Standardization**: Map non-standard verbs to 50+ standard action verbs
- **Service Mapping**: Normalize service names (ECS→ZEC, RDS→DB, OSS→BMC, etc.)
- **Resource Naming**: Apply standard resource type names with PascalCase for composites
- **Cross-Format Support**: Handle English, Chinese, operation codes, and descriptions

## Standard Format

**Required Output Format**: `[Action] [Service] [Resource]`

**Format Rules**:
- Title Case (each word's first letter capitalized)
- Single space between words
- No underscores, hyphens, or special characters
- Standard action verb from dictionary
- Standard service abbreviation
- Standard resource name (PascalCase for composites)

## Reference Documents

This skill uses reference documents in the `references/` directory:

### `references/rule.md`
Contains the complete event naming specification including:
- **Naming Structure**: `[Action] [Service] [Resource]` format
- **Format Rules**: Title Case, single space separator, prohibited symbols
- **Standard Action Dictionary**: 50+ standardized verbs with usage scenarios
- **Service Name Mapping**: Standard service name abbreviations (ZEC, BMC, IAM, DB, Network, Monitor)
- **Resource Name Mapping**: Standard resource type names
- **Processing Workflow**: Step-by-step normalization process
- **Common Errors**: Error patterns and corrections

### `references/example.md`
Contains 15+ practical examples covering:
- Interface description normalization
- Operation code translation
- Format error corrections
- Chinese to English conversion
- Complex resource handling
- Batch operations
- Permission management
- Import/export operations

## Instructions

### Step 1: Input Analysis

When given an interface behavior description or operation code:

1. **Identify Input Format**: Determine the input type
   - Plain text description (e.g., "Query bandwidth cluster usage")
   - Operation code (e.g., "DescribeBandwidthClusterUsage")
   - Snake case (e.g., "create_ecs_instance")
   - Kebab case (e.g., "delete-oss-bucket")
   - Chinese description (e.g., "创建云服务器实例")

2. **Extract Components**:
   - **Action**: The operation being performed
   - **Service**: The business module (may be implicit)
   - **Resource**: The target object (may be composite)

3. **Check for Special Cases**:
   - Batch operations (needs "Batch" prefix)
   - Sub-resources (needs composite resource name)
   - Association operations (needs special handling)

### Step 2: Apply Rules

1. **Normalize Action Verb**
   - Map to standard action from the Action Dictionary (see `references/rule.md`)
   - Consider the operation type (create, update, delete, query, etc.)
   - Example: "query" → "Describe" (for details), "List" (for collections)

2. **Normalize Service Name**
   - Use standard service abbreviations (see `references/rule.md`)
   - Infer service from context if not explicit
   - Examples: "ecs" → "ZEC", "rds" → "DB", "oss" → "BMC"

3. **Normalize Resource Name**
   - Use standard resource type names
   - Apply PascalCase for composite resources
   - Examples: "instance config" → "InstanceConfiguration", "disk storage" → "DiskStorage"

4. **Apply Format Rules**
   - Convert to Title Case (first letter uppercase for each word)
   - Use single space between words
   - Remove prohibited symbols (_, -, ., @, #, etc.)
   - Maintain `[Action] [Service] [Resource]` structure

### Step 3: Validate Output

Ensure the normalized description meets all criteria:
- [ ] Title Case format
- [ ] Single space separator
- [ ] No prohibited symbols
- [ ] Standard action verb
- [ ] Standard service name
- [ ] Standard resource name
- [ ] Proper composite resource naming
- [ ] Matches `[Action] [Service] [Resource]` structure

## Output Format

Provide the normalized result in the following format:

```markdown
## Input Analysis
- **原始输入**: [the input provided]
- **输入类型**: [description/operation code/snake_case/etc.]
- **识别的组件**: [action, service, resource]

## Applied Rules
- **动词规则**: [action mapping and reasoning]
- **服务规则**: [service mapping and reasoning]
- **资源规则**: [resource mapping and reasoning]
- **格式修正**: [format corrections applied]

## Normalized Output
**标准接口行为描述**: `[Action] [Service] [Resource]`

```json
{
  "description": "[Action] [Service] [Resource]",
  "components": {
    "action": "[Action]",
    "service": "[Service]",
    "resource": "[Resource]"
  }
}
```

## Validation Checklist
- [x] Title Case format
- [x] Single space separator
- [x] No prohibited symbols
- [x] Standard action verb
- [x] Standard service name
- [x] Standard resource name
```

## When to Use

Use this skill when:
- User asks to normalize audit logs or interface descriptions
- User mentions standardizing interface behavior
- User provides operation codes that need translation
- User requests format correction (snake_case, kebab-case, etc.)
- User asks about API behavior documentation
- User mentions event naming conventions
- User provides Chinese interface descriptions that need English translation
- User asks to convert non-standard format to standard format
- User mentions keywords: 规范化, 标准化, 接口描述, 接口行为, 操作符, 操作码

## Example Scenarios

### Scenario 1: Interface Description Normalization
**User Input**: "请帮我将接口描述'Query bandwidth cluster usage' 处理成标准接口行为描述"

**Approach**:
1. Extract: Query (action), bandwidth cluster (service context), usage (resource context)
2. Map: Query → Describe, bandwidth cluster → Monitor, usage → ClusterUsage
3. Output: `Describe Monitor ClusterUsage`

### Scenario 2: Operation Code Normalization
**User Input**: "请帮我将接口操作符'DescribeBandwidthClusterUsage' 处理成标准接口行为描述"

**Approach**:
1. Parse: Describe (action), BandwidthClusterUsage (resource)
2. Map: Bandwidth → Monitor service, ClusterUsage → ClusterUsage
3. Output: `Describe Monitor ClusterUsage`

### Scenario 3: Format Error Correction
**User Input**: "create_ecs_instance"

**Approach**:
1. Detect: Snake case format, lowercase
2. Map: create → Create, ecs → ZEC, instance → Instance
3. Apply: Title Case, space separator
4. Output: `Create ZEC Instance`

## Quick Reference

### Standard Service Abbreviations
| Original | Standard |
|----------|----------|
| ECS/云服务器 | ZEC |
| RDS/数据库 | DB |
| OSS/存储 | BMC |
| VPC/网络 | Network |
| IAM/权限 | IAM |
| Monitor/监控 | Monitor |

### Common Action Mappings
| Original | Standard | Usage |
|----------|----------|-------|
| make/build | Create | Create resource |
| add/insert | Add | Add association |
| change/alter | Update/Modify | Modify attribute/spec |
| remove/drop | Delete/Remove | Delete/Remove |
| get/query | Get/List/Describe | Query/Get |

## Important Notes

- **Always reference** `references/rule.md` for the complete specification
- **Use examples** from `references/example.md` to validate output format
- **Maintain semantic meaning** while normalizing format
- **Infer context** when service or resource is not explicit
- **Preserve technical accuracy** during translation
- **Apply strict format rules**: Title Case, single space, no symbols
