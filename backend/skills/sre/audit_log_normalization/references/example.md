# 审计日志规范化示例

本文档提供审计日志规范化的具体示例，展示如何将各种类型的接口行为描述转换为标准格式。

---

## 示例 1: 接口描述规范化

### 输入
```
请帮我将接口描述"Query bandwidth cluster usage" 处理成标准接口行为描述。
```

### 分析过程
1. **识别操作类型**: Query（查询） → 标准化为 **Describe**
2. **识别服务模块**: bandwidth → 隐含监控服务 → **Monitor**
3. **识别资源对象**: cluster usage → **ClusterUsage**（复合资源）

### 规则应用
- **动词规则**: 查询类操作，获取详情用 Describe
- **服务规则**: bandwidth 相关 → Monitor 服务
- **资源规则**: cluster usage → ClusterUsage（帕斯卡命名）

### 规范化输出
**标准接口行为描述**: `Describe Monitor ClusterUsage`

---

## 示例 2: 操作符规范化

### 输入
```
请帮我将接口操作符"DescribeBandwidthClusterUsage" 处理成标准接口行为描述。
```

### 分析过程
1. **拆分操作符**: Describe Bandwidth Cluster Usage
2. **识别操作类型**: Describe（已经是标准动词）
3. **识别服务模块**: Bandwidth → **Monitor**
4. **识别资源对象**: ClusterUsage（保持不变）

### 规则应用
- **动词规则**: Describe 是标准动词，保持不变
- **服务规则**: Bandwidth → Monitor（标准化服务名）
- **格式规则**: 拆分为独立单词，用空格分隔

### 规范化输出
**标准接口行为描述**: `Describe Monitor ClusterUsage`

---

## 示例 3: 格式错误修正（下划线）

### 输入
```
create_ecs_instance
```

### 分析过程
1. **识别错误**: 使用下划线分隔，全小写
2. **提取组件**: create / ecs / instance
3. **应用标准化**:
   - create → **Create**
   - ecs → **ZEC**（云服务器标准名）
   - instance → **Instance**

### 规则应用
- **格式规则**: 下划线改为空格，全小写改为 Title Case
- **服务规则**: ecs → ZEC
- **资源规则**: instance → Instance

### 规范化输出
**标准接口行为描述**: `Create ZEC Instance`

---

## 示例 4: 格式错误修正（连字符）

### 输入
```
delete-oss-bucket
```

### 分析过程
1. **识别错误**: 使用连字符分隔
2. **提取组件**: delete / oss / bucket
3. **应用标准化**:
   - delete → **Delete**
   - oss → **BMC**（存储服务标准名）
   - bucket → **Bucket**

### 规则应用
- **格式规则**: 连字符改为空格，首字母大写
- **服务规则**: oss → BMC
- **资源规则**: bucket → Bucket

### 规范化输出
**标准接口行为描述**: `Delete BMC Bucket`

---

## 示例 5: 规格修改操作

### 输入
```
update_rds_instance_spec
```

### 分析过程
1. **提取组件**: update / rds / instance / spec
2. **识别操作类型**: 修改规格 → **Modify**（而非 Update）
3. **应用标准化**:
   - update → **Modify**（涉及硬件规格）
   - rds → **DB**（数据库标准名）
   - instance spec → **InstanceSpec**（复合资源）

### 规则应用
- **动词规则**: 涉及规格/硬件参数修改用 Modify
- **服务规则**: rds → DB
- **资源规则**: instance spec → InstanceSpec

### 规范化输出
**标准接口行为描述**: `Modify DB InstanceSpec`

---

## 示例 6: 列表查询操作

### 输入
```
get_user_list
```

### 分析过程
1. **识别操作类型**: get list → 获取列表 → **List**
2. **识别服务模块**: user → 隐含 IAM 服务 → **IAM**
3. **识别资源对象**: user → **User**

### 规则应用
- **动词规则**: 获取列表用 List（而非 Get）
- **服务规则**: 用户相关 → IAM
- **资源规则**: user → User

### 规范化输出
**标准接口行为描述**: `List IAM User`

---

## 示例 7: 挂载资源操作

### 输入
```
attach_disk_to_instance
```

### 分析过程
1. **提取组件**: attach / disk / to / instance
2. **应用标准化**:
   - attach → **Attach**
   - disk → **DiskStorage**（复合资源）
   - instance → 隐含 ZEC 服务

### 规则应用
- **动词规则**: 挂载操作用 Attach
- **服务规则**: 实例和磁盘操作 → ZEC
- **资源规则**: disk storage → DiskStorage

### 规范化输出
**标准接口行为描述**: `Attach ZEC DiskStorage`

---

## 示例 8: 批量操作

### 输入
```
batch_create_instances
```

### 分析过程
1. **提取组件**: batch / create / instances
2. **应用标准化**:
   - batch + create → **BatchCreate**
   - instances → **Instance**（保持单数）
   - 隐含 ZEC 服务

### 规则应用
- **动词规则**: 批量操作添加 Batch 前缀
- **资源规则**: instances → Instance（单数形式）

### 规范化输出
**标准接口行为描述**: `BatchCreate ZEC Instance`

---

## 示例 9: 权限绑定

### 输入
```
bind_policy_to_user
```

### 分析过程
1. **提取组件**: bind / policy / to / user
2. **应用标准化**:
   - bind → **Bind**
   - policy → 隐含 IAM 服务 → **IAM**
   - user → User

### 规则应用
- **动词规则**: 绑定操作用 Bind
- **服务规则**: 策略和用户 → IAM

### 规范化输出
**标准接口行为描述**: `Bind IAM Policy`

---

## 示例 10: 中文描述转换

### 输入
```
创建云服务器实例
```

### 分析过程
1. **翻译**: 创建 → Create，云服务器 → ZEC，实例 → Instance
2. **应用标准化**:
   - 创建 → **Create**
   - 云服务器 → **ZEC**
   - 实例 → **Instance**

### 规则应用
- **中英映射**: 创建 → Create
- **服务规则**: 云服务器 → ZEC
- **资源规则**: 实例 → Instance

### 规范化输出
**标准接口行为描述**: `Create ZEC Instance`

---

## 示例 11: 帕斯卡命名拆分

### 输入
```
UpdateInstanceConfiguration
```

### 分析过程
1. **拆分**: Update Instance Configuration
2. **应用标准化**:
   - Update → **Update**
   - Instance Configuration → **InstanceConfiguration**（复合资源）

### 规则应用
- **格式规则**: 帕斯卡命名 → 拆分为独立单词
- **资源规则**: Instance Configuration → InstanceConfiguration

### 规范化输出
**标准接口行为描述**: `Update ZEC InstanceConfiguration`

---

## 示例 12: 密码重置操作

### 输入
```
重置数据库实例root密码
```

### 分析过程
1. **翻译**: 重置 → Reset，数据库 → DB，实例root密码 → 实例属性
2. **应用标准化**:
   - 重置 → **Reset**
   - 数据库 → **DB**
   - 实例root密码 → 简化为 **Instance**

### 规则应用
- **动词规则**: 重置密码 → Reset
- **资源简化**: root密码作为实例属性，简化为 Instance

### 规范化输出
**标准接口行为描述**: `Reset DB Instance`

---

## 示例 13: 子资源操作

### 输入
```
get_instance_console_url
```

### 分析过程
1. **提取组件**: get / instance / console / url
2. **应用标准化**:
   - get → **Get**（获取特定值）
   - instance console url → **InstanceConsoleUrl**（复合资源）

### 规则应用
- **动词规则**: 获取URL等特定值用 Get
- **资源规则**: instance console url → InstanceConsoleUrl

### 规范化输出
**标准接口行为描述**: `Get ZEC InstanceConsoleUrl`

---

## 示例 14: 导出操作

### 输入
```
export_billing_records
```

### 分析过程
1. **提取组件**: export / billing / records
2. **应用标准化**:
   - export → **Export**
   - billing → **Billing**
   - records → **Record**（单数形式）

### 规则应用
- **动词规则**: 导出用 Export
- **服务规则**: 计费相关 → Billing
- **资源规则**: records → Record

### 规范化输出
**标准接口行为描述**: `Export Billing Record`

---

## 示例 15: 启动操作

### 输入
```
start_ecs_server
```

### 分析过程
1. **提取组件**: start / ecs / server
2. **应用标准化**:
   - start → **Start**
   - ecs → **ZEC**
   - server → **Instance**（服务器统一为实例）

### 规则应用
- **动词规则**: 启动用 Start
- **服务规则**: ecs → ZEC
- **资源规则**: server → Instance

### 规范化输出
**标准接口行为描述**: `Start ZEC Instance`

---

## 快速参考表

### 常见错误与修正对照表

| 原始输入 | 问题类型 | 规范化输出 |
|---|---|---|
| `create_ecs_instance` | 下划线+小写 | `Create ZEC Instance` |
| `delete-oss-bucket` | 连字符 | `Delete BMC Bucket` |
| `update_rds_spec` | 非标准服务名+动词选择 | `Modify DB InstanceSpec` |
| `get_user_list` | 动词选择错误 | `List IAM User` |
| `make_server` | 非标准动词+服务名 | `Create ZEC Instance` |
| `Create-ZEC-Instance` | 连字符分隔 | `Create ZEC Instance` |
| `CREATE ZEC INSTANCE` | 全大写 | `Create ZEC Instance` |

### 服务名称映射表

| 原始名称 | 标准名称 | 说明 |
|---|---|---|
| ECS / 云服务器 / VM | ZEC | 云服务器 |
| RDS / 数据库 / DB | DB | 数据库 |
| OSS / 存储 / 对象存储 | BMC | 对象存储 |
| VPC / 网络 | Network | 网络服务 |
| IAM / 身份认证 / 权限 | IAM | 身份管理 |
| Monitor / 监控 | Monitor | 监控服务 |

### 标准动词选择表

| 操作类型 | 标准动词 | 使用条件 |
|---|---|---|
| 创建独立实体 | **Create** | 产生新的资源 ID |
| 添加关联 | **Add** | 资源已存在，仅增加关联 |
| 修改属性 | **Update** | 修改可配置属性 |
| 修改规格 | **Modify** | 修改硬件/规格参数 |
| 永久删除 | **Delete** | 资源被移除 |
| 移除关联 | **Remove** | 解除关联关系 |
| 获取列表 | **List** | 返回集合/数组 |
| 查看详情 | **Describe** | 返回单个对象详情 |
| 获取特定值 | **Get** | 获取敏感或动态值 |

### 资源复合命名示例

| 原始表达 | 标准复合资源 | 说明 |
|---|---|---|
| instance config | **InstanceConfiguration** | 实例配置 |
| disk storage | **DiskStorage** | 磁盘存储 |
| security group | **SecurityGroup** | 安全组 |
| console url | **ConsoleUrl** | 控制台URL |
| access key | **AccessKey** | 访问密钥 |
| user group | **UserGroup** | 用户组 |
| instance terminal | **InstanceTerminal** | 实例终端 |

---

## 输出格式要求

所有规范化输出必须严格遵循以下格式：

```
[Action] [Service] [Resource]
```

**格式要求**：
1. ✅ Title Case（每个单词首字母大写）
2. ✅ 单个半角空格分隔
3. ✅ 不包含下划线、连字符等符号
4. ✅ 使用标准动词词典中的动词
5. ✅ 使用标准服务名称缩写
6. ✅ 使用标准资源类型名称
7. ✅ 复合资源使用帕斯卡命名法
