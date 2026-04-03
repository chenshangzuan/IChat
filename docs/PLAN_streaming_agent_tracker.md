# 流式聊天模式支持 AgentTracker 追踪

## 概述

为流式聊天模式添加 AgentTracker 支持，使其能够像非流式模式一样追踪代理委托、工具调用、skill 调用等统计信息。

## 当前状态分析

### 非流式模式 (已有完整 AgentTracker 集成)
- 文件: `backend/demos/deepagents_demo.py:157-213`
- 函数: `chat_response_with_metadata`
- 特性:
  - 创建 `AgentTracker(session_id)`
  - 调用 `tracker.log_session_start(user_input)`
  - 调用 `tracker.detect_and_log_tool_calls(result["messages"])`
  - 调用 `tracker.log_session_complete()`
  - 返回包含 `tracker_summary` 的完整元数据

### 流式模式 (无 AgentTracker 集成)
- 文件: `backend/demos/deepagents_demo.py:216-233`
- 函数: `chat_stream`
- 特性:
  - 仅使用 `orchestrator.astream()` 流式传输内容
  - **没有 AgentTracker 集成**
  - **不返回任何元数据**

### 前端当前逻辑
- 文件: `frontend/src/stores/chat.ts:88-111`
- `deepagents` demo 使用非流式 (`sendMessage`) 以获取 agent 元数据
- 其他 demo 使用流式 (`sendMessageStream`)

## 技术方案：SSE 尾部追加元数据

**核心思路**: 在流式传输完成后，通过特殊分隔符追加元数据 JSON。

### 实现步骤

#### 步骤 1: 后端 - 创建带元数据的流式函数

**文件**: `backend/demos/deepagents_demo.py`

在 `chat_stream` 函数后添加新函数 `chat_stream_with_metadata`：

```python
async def chat_stream_with_metadata(user_input: str, session_id: str = "default") -> AsyncIterator[str]:
    """
    流式聊天响应（包含元数据）

    在流式传输完成后，通过特殊分隔符追加 AgentTracker 元数据。

    Args:
        user_input: 用户输入
        session_id: 会话 ID

    Yields:
        Agent 的响应文本片段，最后追加分隔符和元数据
    """
    import json

    # 创建跟踪器
    tracker = AgentTracker(session_id)
    tracker.log_session_start(user_input)

    logger.info("=" * 60)
    logger.info(f"🔵 [DeepAgents Stream] 收到请求")
    logger.info(f"  Session ID: {session_id}")
    logger.info(f"  用户输入: {user_input[:100]}...")
    logger.info("=" * 60)

    # 收集所有消息用于 AgentTracker 分析
    all_messages = []
    full_response = ""

    # 流式传输内容
    async for chunk in orchestrator.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        stream_mode="messages"
    ):
        if hasattr(chunk, 'content'):
            content = chunk.content
            full_response += content
            all_messages.append(chunk)
            yield content

    # 使用跟踪器分析消息历史
    tracker.detect_and_log_tool_calls(all_messages)

    # 检测 agent 类型
    detected_agent = detect_agent(full_response)

    tracker.log_session_complete()

    # 追加分隔符和元数据
    metadata = {
        "agent": detected_agent,
        "tracker_summary": tracker.get_summary(),
    }

    # 使用特殊的分隔符标记元数据开始
    yield "\n\n---METADATA---\n"
    yield json.dumps(metadata, ensure_ascii=False)
```

#### 步骤 2: 后端 - 更新流式端点

**文件**: `backend/main.py:221-272`

修改 `chat_stream_endpoint` 函数，使用新的带元数据的流式函数：

```python
@app.post("/api/chat/stream", tags=["聊天"])
async def chat_stream_endpoint(request: ChatRequest):
    """流式聊天接口（支持元数据）"""
    async def generate():
        try:
            logger.info(f"📨 收到流式聊天请求: demo={request.demo_id}, session={request.session_id}")

            if request.demo_id == "basic-chat":
                # Basic Chat Demo（无元数据）
                async for chunk in basic_chat.chat_stream(
                    user_input=request.message,
                    session_id=request.session_id
                ):
                    yield chunk

            elif request.demo_id == "deepagents":
                # DeepAgents Demo（包含元数据）
                async for chunk in deepagents_demo.chat_stream_with_metadata(
                    user_input=request.message,
                    session_id=request.session_id
                ):
                    yield chunk

            else:
                yield f"错误: 未知的 demo_id: {request.demo_id}"
                return

            logger.info(f"✅ 流式聊天响应完成: session={request.session_id}")

        except Exception as e:
            logger.error(f"❌ 流式聊天处理失败: {e}")
            yield f"\n[错误: {str(e)}]"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

#### 步骤 3: 前端 - 更新流式 API 函数

**文件**: `frontend/src/api/chat.ts:56-95`

修改 `sendMessageStream` 函数，解析元数据：

```typescript
export async function sendMessageStream(
  message: string,
  onChunk: (chunk: string) => void,
  sessionId = 'default',
  demoId = 'basic-chat'
): Promise<{ agentMetadata?: AgentMetadata }> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      demo_id: demoId,
    }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No response body')
  }

  let buffer = ''
  let agentMetadata: AgentMetadata | undefined

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    buffer += chunk

    // 检查是否包含元数据分隔符
    const metadataIndex = buffer.indexOf('\n\n---METADATA---\n')
    if (metadataIndex !== -1) {
      // 分离内容和元数据
      const content = buffer.substring(0, metadataIndex)
      const metadataJson = buffer.substring(metadataIndex + '\n\n---METADATA---\n'.length)

      // 发送最后的内容块
      if (content) {
        onChunk(content)
      }

      // 解析元数据
      try {
        const metadata = JSON.parse(metadataJson)
        const trackerSummary = metadata.tracker_summary || {}

        // 提取 skill 名称列表
        const skillCallsData = trackerSummary.skill_calls || []
        const skillNames = skillCallsData
          .map((call: any) => call.skill_name)
          .filter((name: string) => name)

        agentMetadata = {
          agent_type: metadata.agent,
          delegations: trackerSummary.delegation_count || 0,
          tool_calls: trackerSummary.tool_call_count || 0,
          skill_calls: trackerSummary.skill_call_count || 0,
          skills: skillNames,
          duration: trackerSummary.duration || 0,
        }
      } catch (e) {
        console.error('Failed to parse metadata:', e)
      }

      break
    } else {
      // 没有元数据，发送内容（保留可能不完整的最后一块）
      const lastNewlineIndex = buffer.lastIndexOf('\n')
      if (lastNewlineIndex !== -1) {
        onChunk(buffer.substring(0, lastNewlineIndex + 1))
        buffer = buffer.substring(lastNewlineIndex + 1)
      }
    }
  }

  return { agentMetadata }
}
```

#### 步骤 4: 前端 - 更新 Store 使用流式模式

**文件**: `frontend/src/stores/chat.ts:60-117`

修改 `sendMessageAndReceive` 函数，让 `deepagents` demo 也使用流式模式：

```typescript
async function sendMessageAndReceive(userMessage: string) {
  // ... 省略前面的代码 ...

  try {
    // 所有 demo 都使用流式接收响应
    const { agentMetadata } = await sendMessageStream(
      userMessage,
      (chunk) => {
        assistantMsg.content += chunk
      },
      sessionId.value,
      currentDemo.value
    )

    // 保存 agent 元数据（如果有）
    if (agentMetadata) {
      assistantMsg.agentMetadata = agentMetadata
    }
  } catch (error) {
    // ... 错误处理 ...
  }
}
```

## 关键文件

| 文件 | 修改内容 |
|------|----------|
| `backend/demos/deepagents_demo.py` | 添加 `chat_stream_with_metadata` 函数 |
| `backend/main.py` | 更新流式端点使用新函数 |
| `frontend/src/api/chat.ts` | 修改 `sendMessageStream` 解析元数据 |
| `frontend/src/stores/chat.ts` | 让 `deepagents` 也使用流式模式 |

## 验证测试

### 测试步骤

1. **启动后端服务**:
   ```bash
   cd backend
   uv run uvicorn main:app --reload --port 8000
   ```

2. **启动前端服务**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **测试场景**:
   - 打开前端页面
   - 选择 "Multi-Agent System" demo
   - 发送测试消息: "你现在有哪些skills"
   - 验证:
     - [ ] 响应是流式显示（逐字出现）
     - [ ] 响应完成后显示 Agent 徽章和元数据
     - [ ] 委托次数、工具调用、skill 调用统计正确
     - [ ] 使用的 skills 图标显示正确

### 预期结果

- 消息内容流式显示
- 响应完成后显示:
  - Agent 类型 (Orchestrator/Coder/SRE)
  - 委托次数 (如果有的话)
  - 工具调用次数
  - Skill 调用次数
  - 使用的技能图标

## 注意事项

1. **分隔符选择**: 使用 `---METADATA---` 作为分隔符，确保不会与正常内容冲突
2. **JSON 格式**: 元数据使用 `ensure_ascii=False` 确保中文字符正确显示
3. **前端的解析逻辑**: 需要处理跨 chunk 的分隔符情况
4. **向后兼容**: basic-chat demo 仍然不返回元数据
