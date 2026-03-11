import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  sendMessage,
  sendMessageStream,
  clearHistory as clearHistoryApi,
  getDemos,
  type AgentMetadata
} from '@/api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  agentMetadata?: AgentMetadata  // 新增：agent 元数据（仅 deepagents demo）
}

export interface Demo {
  id: string
  name: string
  description: string
  category: string
  coming_soon?: boolean
}

export const useChatStore = defineStore('chat', () => {
  // 状态
  const currentDemo = ref<string>('deepagents')
  const demos = ref<Demo[]>([])
  const isLoading = ref(false)
  const sessionId = ref(`session-${Date.now()}`)

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
    } catch (error) {
      console.error('Failed to load demos:', error)
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

    // 创建一个空的助手消息，用于流式更新
    const assistantMsg: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    currentMessages.push(assistantMsg)
    isLoading.value = true

    try {
      // 根据 demo 类型选择流式或非流式
      // deepagents 使用非流式以获取 agent 元数据
      if (currentDemo.value === 'deepagents') {
        const response = await sendMessage(
          userMessage,
          sessionId.value,
          currentDemo.value
        )
        assistantMsg.content = response.response
        // 保存 agent 元数据
        if (response.agent_metadata) {
          assistantMsg.agentMetadata = response.agent_metadata
        }
      } else {
        // 流式接收响应
        await sendMessageStream(
          userMessage,
          (chunk) => {
            assistantMsg.content += chunk
          },
          sessionId.value,
          currentDemo.value
        )
      }
    } catch (error) {
      assistantMsg.content = `错误: ${error instanceof Error ? error.message : '未知错误'}`
    } finally {
      isLoading.value = false
    }
  }

  async function clearHistory() {
    try {
      await clearHistoryApi(sessionId.value)
      // 只清空当前 demo 的历史
      demoMessages.value.set(currentDemo.value, [])
      // 生成新的 sessionId
      sessionId.value = `session-${Date.now()}`
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

  return {
    messages,
    currentDemo,
    demos,
    isLoading,
    hasMessages,
    sessionId,
    demoMessages,  // 暴露给外部访问
    loadDemos,
    sendMessageAndReceive,
    clearHistory,
    switchDemo,
  }
})
