import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import {
  sendMessage,
  sendMessageStream,
  clearHistory as clearHistoryApi,
  getDemos,
  getHistory,
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

      // 转换为 Message 格式
      const messages: Message[] = history.map((msg, index) => ({
        id: msg.id || `history-${index}`,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || Date.now()
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
      // 所有 demo 都使用流式接收响应
      // deepagents 会在流结束时发送元数据标记
      let fullContent = ''

      await sendMessageStream(
        userMessage,
        (chunk) => {
          // 检查是否是元数据标记
          if (chunk.includes('__METADATA__:')) {
            // 提取元数据
            const metadataMatch = chunk.match(/__METADATA__:(.+)$/)
            if (metadataMatch) {
              try {
                const metadata = JSON.parse(metadataMatch[1])
                // 保存 agent 元数据
                assistantMsg.agentMetadata = metadata
                // 移除元数据标记（不显示在内容中）
                assistantMsg.content = fullContent.replace(/__METADATA__:.+$/, '').trim()
              } catch (e) {
                console.error('Failed to parse metadata:', e)
                assistantMsg.content = fullContent + chunk
              }
            }
          } else {
            // 普通内容，累加并显示
            fullContent += chunk
            assistantMsg.content = fullContent
          }
        },
        sessionId.value,
        currentDemo.value
      )
    } catch (error) {
      assistantMsg.content = `错误: ${error instanceof Error ? error.message : '未知错误'}`
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

  return {
    messages,
    currentDemo,
    demos,
    isLoading,
    hasMessages,
    sessionId,
    demoMessages,  // 暴露给外部访问
    loadDemos,
    loadHistory,
    sendMessageAndReceive,
    clearHistory,
    switchDemo,
  }
})
