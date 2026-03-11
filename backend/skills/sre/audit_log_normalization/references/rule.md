# 事件命名规范 (Event Naming Specification)

本文档定义了审计日志中事件名称的标准化规范，所有接口行为描述必须遵循此规范。

---

## 1. 命名结构 (Schema)

所有事件名称必须遵循以下结构：

```
[Action] [Service] [Resource]
```

**示例**：
- `Create ZEC Instance`
- `Describe Monitor ClusterUsage`
- `Modify DB InstanceSpec`

---

## 2. 格式规范

### 2.1 大小写规则

所有单词必须使用 **Title Case（首字母大写）**：

| 错误示例 | 正确示例 |
|---|---|
| create zec instance | **Create ZEC Instance** |
| CREATE ZEC INSTANCE | **Create ZEC Instance** |
| Create Zec instance | **Create ZEC Instance** |

### 2.2 分隔符规则

单词之间 **只能使用一个半角空格**：

| 错误示例 | 正确示例 |
|---|---|
| Create_ZEC_Instance | **Create ZEC Instance** |
| Create-ZEC-Instance | **Create ZEC Instance** |
| Create  ZEC  Instance | **Create ZEC Instance** |

### 2.3 禁用符号

**禁止使用**以下符号：
- `_` (下划线)
- `-` (连字符)
- `.` (点号)
- `@`, `#`, `$`, `%` 等特殊字符

---

## 3. 标准化动词词典 (Action Dictionary)

### 3.1 创建类 (Creation)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **Create** | 从无到有创建一个独立实体 | 产生新的资源 ID | `Create ZEC Instance` |
| **Add** | 将已有资源加入某个容器或组 | 资源已存在，仅增加关联 | `Add IAM UserGroupMember` |

### 3.2 修改类 (Modification)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **Update** | 修改可配置属性 | 配置类属性修改 | `Update ZEC InstanceName` |
| **Modify** | 修改硬件/规格参数 | 涉及硬件规格 | `Modify DB InstanceSpec` |
| **Reset** | 重置到初始状态 | 密码、配置重置 | `Reset DB InstancePassword` |
| **Change** | 改变状态或状态值 | 状态变更 | `Change ZEC InstanceStatus` |

### 3.3 删除类 (Deletion)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **Delete** | 永久删除资源 | 资源被移除 | `Delete BMC Bucket` |
| **Remove** | 移除关联关系 | 解除关联，资源保留 | `Remove ZEC SecurityGroupMember` |

### 3.4 查询类 (Query)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **List** | 获取列表/集合 | 返回数组/集合 | `List IAM User` |
| **Describe** | 获取单个对象详情 | 返回完整对象信息 | `Describe ZEC Instance` |
| **Get** | 获取特定值 | 获取敏感或动态值 | `Get ZEC InstanceConsoleUrl` |
| **Check** | 检查状态/可用性 | 布尔值判断 | `Check ZEC InstanceName` |
| **Verify** | 验证配置/权限 | 确认类操作 | `Verify IAM UserPermission` |

#### 3.4.1 常见非标准动词映射

**以下动词必须映射到标准查询动词**：

| 非标准动词 | 应映射为 | 映射规则 | 示例 |
|---|---|---|---|
| Query | List/Describe | 获取列表→List，获取详情→Describe | `query user list` → `List IAM User` |
| Search | List | 搜索即查询列表 | `search user` → `List IAM User` |
| Find | List/Describe | 查找即查询 | `find user by id` → `Describe IAM User` |
| Fetch | Get | 获取特定值 | `fetch config` → `Get IAM Config` |
| Retrieve | List/Get | 检索数据 | `retrieve users` → `List IAM User` |
| Show | Describe | 展示详情 | `show user info` → `Describe IAM User` |
| View | Describe | 查看详情 | `view user details` → `Describe IAM User` |
| Read | Get | 读取数据 | `read config` → `Get IAM Config` |

**🚫 关键规则**：
- **"Query" 永远不应作为最终 Action**，必须根据上下文映射到 List/Describe/Get
- 如果是获取列表/集合，使用 **List**
- 如果是获取单个对象详情，使用 **Describe**
- 如果是获取特定属性值，使用 **Get**

### 3.5 管理类 (Management)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **Start** | 启动已停止的资源 | 状态：stopped → running | `Start ZEC Instance` |
| **Stop** | 停止运行中的资源 | 状态：running → stopped | `Stop ZEC Instance` |
| **Restart** | 重启资源 | 先停止再启动 | `Restart ZEC Instance` |
| **Attach** | 挂载资源 | 磁盘、网卡等 | `Attach ZEC DiskStorage` |
| **Detach** | 卸载资源 | 磁盘、网卡等 | `Detach ZEC DiskStorage` |
| **Bind** | 绑定策略/权限 | 策略绑定 | `Bind IAM Policy` |
| **Unbind** | 解绑策略/权限 | 策略解绑 | `Unbind IAM Policy` |
| **Grant** | 授予权限 | 权限授予 | `Grant IAM UserPermission` |
| **Revoke** | 撤销权限 | 权限撤销 | `Revoke IAM UserPermission` |
| **Authorize** | 授权访问 | 访问授权 | `Authorize Network SecurityGroupRule` |
| **Unauthorize** | 取消授权 | 访问取消 | `Unauthorize Network SecurityGroupRule` |

### 3.6 操作类 (Operations)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **BatchCreate** | 批量创建 | 一次创建多个 | `BatchCreate ZEC Instance` |
| **BatchDelete** | 批量删除 | 一次删除多个 | `BatchDelete ZEC Instance` |
| **Export** | 导出数据/记录 | 数据导出 | `Export Billing Record` |
| **Import** | 导入数据/记录 | 数据导入 | `Import IAM User` |
| **Migrate** | 迁移资源/数据 | 跨区域/迁移 | `Migrate DB Instance` |
| **Sync** | 同步数据/状态 | 数据同步 | `Sync IAM UserStatus` |
| **Resize** | 调整大小 | 磁盘/规格调整 | `Resize ZEC DiskStorage` |
| **Scale** | 扩容/缩容 | 实例数量调整 | `Scale ZEC Instance` |
| **Upgrade** | 升级版本/配置 | 版本升级 | `Upgrade DB InstanceVersion` |
| **Downgrade** | 降级版本/配置 | 版本降级 | `Downgrade DB InstanceVersion` |
| **Renew** | 续费 | 订阅续费 | `Renew ZEC Instance` |
| **Release** | 释放资源 | 释放实例 | `Release ZEC Instance` |

### 3.7 标签类 (Label)

| Action | 使用场景 | 判断依据 | 示例 |
|---|---|---|---|
| **Tag** | 添加标签/标记 | 资源打标 | `Tag ZEC Instance` |
| **Untag** | 移除标签/标记 | 移除标签 | `Untag ZEC Instance` |
| **Label** | 添加标签 (Tag 别名) | 资源打标 | `Label ZEC Instance` |
| **Unlabel** | 移除标签 (Untag 别名) | 移除标签 | `Unlabel ZEC Instance` |

---

## 4. 服务名称映射 (Service Name Mapping)

| 原始名称 | 标准名称 | 说明                           |
|---|---|------------------------------|
| ECS, 云服务器, VM, Server, 云主机, EC2 | **ZEC** | 云服务器 (Zcloud Elastic Compute) |
| RDS, 数据库, DB, MySQL, PostgreSQL, Database | **DB** | 数据库服务                        |
| OSS, 存储, 对象存储, Object Storage, S3, Bucket | **BMC** | 对象存储 (Bucket Management Cloud) |
| VPC, 网络, Network, Virtual Private Cloud | **Network** | 网络服务                         |
| IAM, 权限, Permission, 身份认证, Identity, Access | **IAM** | 身份管理                         |
| Monitor, 监控, Monitoring | **Monitor** | 监控服务                         |
| Billing, 计费, 账单, Account | **Billing** | 计费服务                         |
| Security, 安全, Security Group | **Security** | 安全服务                         |
| SLB, Load Balancer, 负载均衡 | **SLB** | 负载均衡                         |
| CDN, Content Delivery Network | **CDN** | 内容分发网络                       |
| AI | **AI** | AI                           |

---

## 5. 资源名称映射 (Resource Name Mapping)

### 5.1 常见资源

| 原始名称 | 标准名称 | 说明 |
|---|---|---|
   | instance, server, vm, 主机, 服务器 | **Instance** | 使用单数形式 |
   | disk, volume, 存储, 磁盘 | **DiskStorage** | 复合资源 |
   | bucket, object | **Bucket** | 对象存储容器 |
   | security group, sg, 安全组 | **SecurityGroup** | 复合资源 |
   | user, 用户 | **User** | |
   | policy, 策略 | **Policy** | |
   | role, 角色 | **Role** | |
   | group, 组 | **Group** | |

### 5.2 复合资源 (PascalCase)

由多个单词组成的资源使用 **PascalCase** 格式（无空格）：

| 表达方式 | 标准复合资源 | 示例 |
|---|---|---|
| instance config | **InstanceConfiguration** | `Update ZEC InstanceConfiguration` |
| disk storage | **DiskStorage** | `Attach ZEC DiskStorage` |
| security group | **SecurityGroup** | `Create Network SecurityGroup` |
| console url | **ConsoleUrl** | `Get ZEC InstanceConsoleUrl` |
| access key | **AccessKey** | `Create IAM AccessKey` |
| user group | **UserGroup** | `Create IAM UserGroup` |
| instance terminal | **InstanceTerminal** | `Get ZEC InstanceTerminal` |
| cluster usage | **ClusterUsage** | `Describe Monitor ClusterUsage` |
| instance spec | **InstanceSpec** | `Modify DB InstanceSpec` |

---

## 6. 处理工作流

### Step 1: 输入分析

1. **识别输入格式**：
   - 纯文本描述：`Query bandwidth cluster usage`
   - 操作码：`DescribeBandwidthClusterUsage`
   - Snake case：`create_ecs_instance`
   - Kebab case：`delete-oss-bucket`
   - 中文描述：`创建云服务器实例`

2. **提取组件**：
   - **Action**：执行的操作
   - **Service**：业务模块（可能隐含）
   - **Resource**：目标对象（可能是复合资源）

3. **检查特殊情况**：
   - 批量操作 → 需要 "Batch" 前缀
   - 子资源 → 需要复合资源名称
   - 关联操作 → 需要特殊处理

### Step 2: 应用规则

1. **标准化动词**：
   - 映射到标准动词词典
   - 考虑操作类型（创建、修改、删除、查询等）

2. **标准化服务名**：
   - 使用服务名称映射表
   - 从上下文推断服务（如果未明确）

3. **标准化资源名**：
   - 使用标准资源类型名称
   - 复合资源使用 PascalCase

4. **应用格式规则**：
   - 转换为 Title Case
   - 使用单个空格分隔
   - 移除禁用符号

### Step 3: 验证输出

确保规范化描述满足所有标准：
- [ ] Title Case 格式
- [ ] 单个空格分隔
- [ ] 无禁用符号
- [ ] 标准动词
- [ ] 标准服务名
- [ ] 标准资源名
- [ ] 复合资源使用 PascalCase
- [ ] 符合 `[Action] [Service] [Resource]` 结构

---

## 7. 常见错误模式

| 输入模式 | 问题类型 | 正确输出 |
|---|---|---|
| `create_ecs_instance` | 下划线 + 小写 | `Create ZEC Instance` |
| `delete-oss-bucket` | 连字符分隔 | `Delete BMC Bucket` |
| `UpdateInstanceConfiguration` | 缺少服务名 | `Update ZEC InstanceConfiguration` |
| `get_user_list` | 动词选择错误 | `List IAM User` |
| `make_server` | 非标准动词/服务名 | `Create ZEC Instance` |
| `Create-ZEC-Instance` | 连字符分隔 | `Create ZEC Instance` |
| `CREATE ZEC INSTANCE` | 全大写 | `Create ZEC Instance` |
| `update_rds_spec` | 非标准服务名 + 动词选择 | `Modify DB InstanceSpec` |
