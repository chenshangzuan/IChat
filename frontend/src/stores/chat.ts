import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import {
  sendMessage,
  sendMessageStream,
  clearHistory as clearHistoryApi,
  getDemos,
  getHistory,
  type AgentMetadata,
  type ToolCallDetail
} from '@/api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool'  // 新增 tool 角色
  content: string
  timestamp: number
  agentMetadata?: AgentMetadata  // agent 元数据（仅 deepagents demo）
  toolInfo?: {               // 工具信息（仅 tool 角色）
    toolName: string
    status: string
  }
}

export interface Demo {
  id: string
  name: string
  description: string
  category: string
  coming_soon?: boolean
}

export const useChatStore = defineStore('chat', () => {
  // 从 localStorage 读取或生成 sessionId
  const storedSessionId = localStorage.getItem('ichat_session_id')

  // 如果有存储的值，使用它；否则生成新的
  let initialSessionId: string
  if (storedSessionId) {
    initialSessionId = storedSessionId
    console.log('[ChatStore] 恢复已有 sessionId:', initialSessionId)
  } else {
    initialSessionId = `session-${Date.now()}`
    localStorage.setItem('ichat_session_id', initialSessionId)
    console.log('[ChatStore] 生成新的 sessionId:', initialSessionId)
  }

  const sessionId = ref(initialSessionId)

  // userId 状态（从 localStorage 读取，默认为空）
  const userId = ref(localStorage.getItem('ichat_user_id') || '')

  function setUserId(id: string) {
    userId.value = id
    if (id) {
      localStorage.setItem('ichat_user_id', id)
    } else {
      localStorage.removeItem('ichat_user_id')
    }
    console.log('[ChatStore] 设置 userId:', id || '(空)')
  }

  // 状态
  const currentDemo = ref<string>('deepagents')
  const demos = ref<Demo[]>([])
  const isLoading = ref(false)

  // 监听 sessionId 变化，自动持久化到 localStorage
  watch(sessionId, (newId) => {
    if (newId !== initialSessionId) {
      localStorage.setItem('ichat_session_id', newId)
      console.log('[ChatStore] 更新 sessionId:', newId)
    }
  })

  // 为每个 demo 维护独立的消息历史
  // 使用 Map 结构：demo_id -> Message[]
  const demoMessages = ref<Map<string, Message[]>>(new Map())

  // 计算属性 - 返回当前 demo 的消息
  const messages = computed(() => demoMessages.value.get(currentDemo.value) || [])

  const hasMessages = computed(() => messages.value.length > 0)

  // 方法
  async function loadDemos() {
    try {
      const data = await getDemos()
      demos.value = data.demos

      // 初始化每个 demo 的消息历史
      data.demos.forEach(demo => {
        if (!demoMessages.value.has(demo.id)) {
          demoMessages.value.set(demo.id, [])
        }
      })

      // 自动加载当前 demo 的历史记录
      await loadHistory()
    } catch (error) {
      console.error('Failed to load demos:', error)
    }
  }

  async function loadHistory() {
    try {
      // 从后端加载历史消息
      const history = await getHistory(sessionId.value, currentDemo.value)

      // 转换为 Message 格式，保留所有字段
      const messages: Message[] = history.map((msg, index) => ({
        id: msg.id || `history-${index}`,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || Date.now(),
        // 保留工具信息
        toolInfo: msg.toolInfo,
        // 保留 agent 元数据
        agentMetadata: msg.agentMetadata
      }))

      // 恢复到当前 demo 的消息历史
      if (messages.length > 0) {
        demoMessages.value.set(currentDemo.value, messages)
        console.log(`[ChatStore] 已加载 ${messages.length} 条历史消息`)
      }
    } catch (error) {
      console.error('Failed to load history:', error)
      // 如果加载失败，保持空数组
      if (!demoMessages.value.has(currentDemo.value)) {
        demoMessages.value.set(currentDemo.value, [])
      }
    }
  }

  async function sendMessageAndReceive(userMessage: string) {
    // 确保当前 demo 有消息数组
    if (!demoMessages.value.has(currentDemo.value)) {
      demoMessages.value.set(currentDemo.value, [])
    }

    const currentMessages = demoMessages.value.get(currentDemo.value)!

    // 添加用户消息
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userMessage,
      timestamp: Date.now(),
    }
    currentMessages.push(userMsg)

    isLoading.value = true

    // 流式处理状态
    let currentAssistantMsg: Message | null = null
    let currentContent = ''
    let streamedMetadata: AgentMetadata | undefined
    let assistantMsgCount = 0

    // 辅助函数：确保有当前助手消息
    const ensureAssistantMsg = () => {
      if (!currentAssistantMsg) {
        assistantMsgCount++
        currentAssistantMsg = {
          id: `assistant-${Date.now()}-${assistantMsgCount}`,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
        }
        currentMessages.push(currentAssistantMsg)
      }
    }

    try {
      await sendMessageStream(
        userMessage,
        (chunk) => {
          // 按行分割处理
          const lines = chunk.split('\n')

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i]

            // 检查是否是事件行
            if (line.startsWith('__EVENT__:')) {
              try {
                const eventData = JSON.parse(line.substring('__EVENT__:'.length))
                if (eventData.type === 'tool_call') {
                  // 工具调用时，结束当前助手消息
                  if (currentAssistantMsg) {
                    currentAssistantMsg.content = currentContent.trim()
                    currentAssistantMsg = null
                    currentContent = ''
                  }

                  // 创建工具消息
                  const toolMsg: Message = {
                    id: `tool-${Date.now()}-${assistantMsgCount}`,
                    role: 'tool',
                    content: eventData.output,
                    timestamp: Date.now(),
                    toolInfo: {
                      toolName: eventData.tool_name,
                      status: eventData.status
                    }
                  }
                  currentMessages.push(toolMsg)
                  console.log(`[ChatStore] 收到工具事件: ${eventData.tool_name}`)
                }
              } catch (e) {
                console.error('Failed to parse event:', e, line)
              }
            }
            // 检查是否是元数据行
            else if (line.startsWith('__METADATA__:')) {
              try {
                streamedMetadata = JSON.parse(line.substring('__METADATA__:'.length))
                if (currentAssistantMsg) {
                  currentAssistantMsg.agentMetadata = streamedMetadata
                }
              } catch (e) {
                console.error('Failed to parse metadata:', e)
              }
            }
            // 普通内容行
            else if (line) {
              currentContent += (currentContent ? '\n' : '') + line
              ensureAssistantMsg()
              currentAssistantMsg!.content = currentContent
            }
          }
        },
        sessionId.value,
        currentDemo.value,
        userId.value
      )

      // 流式结束后，确保最后的内容已更新
      if (currentAssistantMsg) {
        currentAssistantMsg.content = currentContent.trim()
        if (streamedMetadata) {
          currentAssistantMsg.agentMetadata = streamedMetadata
        }
      }

    } catch (error) {
      const errorMsg = `错误: ${error instanceof Error ? error.message : '未知错误'}`
      if (currentAssistantMsg) {
        currentAssistantMsg.content = errorMsg
      } else {
        currentMessages.push({
          id: `assistant-${Date.now()}-error`,
          role: 'assistant',
          content: errorMsg,
          timestamp: Date.now(),
        })
      }
    } finally {
      isLoading.value = false
    }
  }

  async function clearHistory() {
    try {
      await clearHistoryApi(sessionId.value, currentDemo.value)
      // 只清空当前 demo 的历史
      demoMessages.value.set(currentDemo.value, [])
      // 注意：不再重新生成 sessionId，保持连续性
      // 这样页面刷新后仍然使用同一个 session，可以恢复历史
    } catch (error) {
      console.error('Failed to clear history:', error)
      throw error
    }
  }

  function switchDemo(demoId: string) {
    const demo = demos.value.find(d => d.id === demoId)
    if (!demo || demo.coming_soon) {
      return false
    }

    // 切换 demo（历史会自动切换，因为 messages 是计算属性）
    currentDemo.value = demoId
    return true
  }

  function startNewChat() {
    // 生成新的 sessionId
    const newSessionId = `session-${Date.now()}`
    sessionId.value = newSessionId

    // 清空当前 demo 的消息
    demoMessages.value.set(currentDemo.value, [])

    console.log('[ChatStore] 开始新聊天:', newSessionId)
  }

  return {
    messages,
    currentDemo,
    demos,
    isLoading,
    hasMessages,
    sessionId,
    userId,
    setUserId,
    demoMessages,  // 暴露给外部访问
    loadDemos,
    loadHistory,
    sendMessageAndReceive,
    clearHistory,
    switchDemo,
    startNewChat,
  }
})
