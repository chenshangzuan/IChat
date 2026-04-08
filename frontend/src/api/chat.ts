/**
 * 聊天 API
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,  // 5 分钟超时（Multi-Agent 任务可能需要更长时间）
})

/**
 * 工具调用详情
 */
export interface ToolCallDetail {
  tool_name: string   // 工具名称
  output: string      // 工具输出内容
  status: string      // 状态：completed, failed
}

/**
 * Agent 元数据（Multi-Agent System）
 */
export interface AgentMetadata {
  agent_type?: string  // agent 类型：orchestrator, coder, sre, unknown
  delegations: number  // 委托次数
  tool_calls: number  // 工具调用次数
  skill_calls: number  // skill 调用次数
  skills: string[]  // 使用的 skill 名称列表
  duration: number  // 耗时（秒）
  tool_calls_detail?: ToolCallDetail[]  // 工具调用详情列表
}

/**
 * 聊天响应
 */
export interface ChatResponseData {
  response: string
  session_id: string
  agent_metadata?: AgentMetadata  // 新增：agent 元数据
}

/**
 * 获取可用的 demo 列表
 */
export async function getDemos() {
  const response = await api.get('/demos')
  return response.data
}

/**
 * 发送聊天消息（非流式）
 */
export async function sendMessage(
  message: string,
  sessionId = 'default',
  demoId = 'basic-chat',
  userId = ''
): Promise<ChatResponseData> {
  const response = await api.post('/chat', {
    message,
    session_id: sessionId,
    demo_id: demoId,
    user_id: userId,
  })
  return response.data
}

/**
 * 发送聊天消息（流式）
 */
export async function sendMessageStream(
  message: string,
  onChunk: (chunk: string) => void,
  sessionId = 'default',
  demoId = 'basic-chat',
  userId = ''
) {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      demo_id: demoId,
      user_id: userId,
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

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    onChunk(chunk)
  }
}

/**
 * 发送审批决策（流式）
 */
export async function sendApprovalStream(
  decisions: Array<{ type: string; message?: string }>,
  onChunk: (chunk: string) => void,
  sessionId = 'default',
  demoId = 'deepagents',
  userId = ''
) {
  const response = await fetch('/api/chat/approve', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      demo_id: demoId,
      user_id: userId,
      decisions,
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

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    onChunk(chunk)
  }
}

/**
 * 清空对话历史
 */
export async function clearHistory(
  sessionId = 'default',
  demoId = 'deepagents'  // 新增：指定 demo_id
) {
  const response = await api.post('/chat/clear', {
    session_id: sessionId,
    demo_id: demoId,
  })
  return response.data
}

/**
 * 获取对话历史消息
 */
export interface HistoryMessage {
  id: string
  role: 'user' | 'assistant' | 'tool'
  content: string
  timestamp: number
  toolInfo?: {
    toolName: string
    status: string
  }
  agentMetadata?: AgentMetadata
}

export async function getHistory(
  sessionId: string,
  demoId = 'deepagents'
): Promise<HistoryMessage[]> {
  const response = await api.get('/chat/history', {
    params: { session_id: sessionId, demo_id: demoId }
  })
  return response.data
}
