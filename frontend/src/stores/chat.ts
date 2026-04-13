import { defineStore } from 'pinia'
import { ref, computed, watch, triggerRef } from 'vue'
import {
  sendMessage,
  sendMessageStream,
  sendApprovalStream,
  clearHistory as clearHistoryApi,
  editMessageApi,
  getDemos,
  getHistory,
  getSessions,
  deleteSession as deleteSessionApi,
  type AgentMetadata,
  type ToolCallDetail,
  type ChatSession,
  type SSEEvent
} from '@/api/chat'

export interface ApprovalAction {
  name: string
  args: Record<string, any>
  description: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'approval'
  content: string
  timestamp: number
  agentMetadata?: AgentMetadata  // agent 元数据（仅 deepagents demo）
  toolInfo?: {               // 工具信息（仅 tool 角色）
    toolName: string
    status: string
  }
  approvalInfo?: {           // 审批信息（仅 approval 角色）
    actions: ApprovalAction[]
    timestamp: string
    status: 'pending' | 'approved' | 'rejected'
  }
}

export interface Demo {
  id: string
  name: string
  description: string
  category: string
  coming_soon?: boolean
}

/**
 * 打字机动画控制器
 * 使用 requestAnimationFrame 逐步显示流式文本，实现逐字渲染效果。
 */
function createTypingAnimator(onContentChange?: () => void) {
  let fullContent = ''
  let displayedIdx = 0
  let rafId: number | null = null
  let targetMsg: Message | null = null
  let resolveWait: (() => void) | null = null
  let scrollCb: (() => void) | null = null

  function notifyChange() {
    if (onContentChange) onContentChange()
    if (scrollCb) scrollCb()
  }

  function animate() {
    if (!targetMsg) return
    const pending = fullContent.length - displayedIdx
    if (pending <= 0) {
      rafId = null
      if (resolveWait) { resolveWait(); resolveWait = null }
      return
    }
    // 动态速度：始终逐字或小幅追赶，确保视觉效果可见
    // 积压少时逐字，积压多时每帧最多 3 字符
    const step = Math.min(3, Math.max(1, Math.ceil(pending / 60)))
    displayedIdx = Math.min(displayedIdx + step, fullContent.length)
    targetMsg.content = fullContent.substring(0, displayedIdx)
    notifyChange()
    rafId = requestAnimationFrame(animate)
  }

  return {
    /** 更新目标内容，启动/继续动画 */
    update(msg: Message, content: string) {
      targetMsg = msg
      fullContent = content
      if (!rafId) rafId = requestAnimationFrame(animate)
    },
    /** 立即显示全部内容，停止动画 */
    flush() {
      if (rafId) { cancelAnimationFrame(rafId); rafId = null }
      if (targetMsg) { targetMsg.content = fullContent; displayedIdx = fullContent.length }
      if (resolveWait) { resolveWait(); resolveWait = null }
      notifyChange()
    },
    /** flush + 重置所有状态（用于消息切换） */
    reset() {
      this.flush()
      fullContent = ''
      displayedIdx = 0
      targetMsg = null
    },
    /** 等待动画追赶完成 */
    waitComplete(): Promise<void> {
      if (displayedIdx >= fullContent.length) return Promise.resolve()
      return new Promise(resolve => { resolveWait = resolve })
    },
    /** 注册滚动回调 */
    onScroll(cb: () => void) { scrollCb = cb },
  }
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

  // 打字机动画控制器（每帧 triggerRef 强制 Vue 检测到原始对象的 content 变更）
  const typingAnimator = createTypingAnimator(() => triggerRef(demoMessages))

  function registerScrollCallback(cb: () => void) {
    typingAnimator.onScroll(cb)
  }

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
      const messages: Message[] = history.map((msg: any, index: number) => ({
        id: msg.id || `history-${index}`,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || Date.now(),
        // 保留工具信息
        toolInfo: msg.toolInfo,
        // 保留 agent 元数据
        agentMetadata: msg.agentMetadata,
        // 保留审批信息
        approvalInfo: msg.approvalInfo
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
        console.log('[ChatStore] 创建新的助手消息, count:', assistantMsgCount)
        currentMessages.push({
          id: `assistant-${Date.now()}-${assistantMsgCount}`,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
        })
        // 从响应式数组读回 Proxy 包装的对象，后续修改 .content 才能触发 Vue 响应式
        currentAssistantMsg = currentMessages[currentMessages.length - 1]
        console.log('[ChatStore] 消息列表长度:', currentMessages.length)
      }
    }

    try {
      await sendMessageStream(
        userMessage,
        (event: SSEEvent) => {
          console.log('[ChatStore] 收到SSE事件:', event)
          switch (event.event) {
            case 'message': {
              // 普通文本 token
              console.log('[ChatStore] message事件, 累积内容:', event.data)
              currentContent += event.data
              ensureAssistantMsg()
              console.log('[ChatStore] 当前消息:', currentAssistantMsg)
              typingAnimator.update(currentAssistantMsg!, currentContent)
              break
            }
            case 'tool_call': {
              // 工具调用：立即显示当前内容，创建工具消息
              typingAnimator.reset()
              if (currentAssistantMsg) {
                currentAssistantMsg.content = currentContent.trim()
                currentAssistantMsg = null
                currentContent = ''
              }
              try {
                const eventData = JSON.parse(event.data)

                // 如果tool调用来自sub-agent（coder-agent/sre-agent），将内容作为assistant消息显示
                const isSubAgent = eventData.tool_name === 'coder-agent' || eventData.tool_name === 'sre-agent'

                if (isSubAgent && eventData.output) {
                  // Sub-agent响应作为assistant消息
                  assistantMsgCount++
                  const assistantMsg: Message = {
                    id: `assistant-${Date.now()}-${assistantMsgCount}`,
                    role: 'assistant',
                    content: eventData.output,
                    timestamp: Date.now(),
                  }
                  currentMessages.push(assistantMsg)
                  console.log(`[ChatStore] Sub-agent响应作为assistant消息: ${eventData.tool_name}`)
                } else {
                  // 普通工具调用，显示为工具消息
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
                console.error('Failed to parse tool_call event:', e)
              }
              break
            }
            case 'approval': {
              // 审批请求：立即显示当前内容，创建审批消息
              typingAnimator.reset()
              if (currentAssistantMsg) {
                currentAssistantMsg.content = currentContent.trim()
                currentAssistantMsg = null
                currentContent = ''
              }
              try {
                const eventData = JSON.parse(event.data)
                const approvalMsg: Message = {
                  id: `approval-${Date.now()}`,
                  role: 'approval',
                  content: eventData.actions.map((a: any) =>
                    `${a.name}: ${JSON.stringify(a.args)}`
                  ).join('\n'),
                  timestamp: Date.now(),
                  approvalInfo: {
                    actions: eventData.actions,
                    timestamp: eventData.timestamp,
                    status: 'pending',
                  }
                }
                currentMessages.push(approvalMsg)
                console.log(`[ChatStore] 收到审批事件: ${eventData.actions.map((a: any) => a.name)}`)
              } catch (e) {
                console.error('Failed to parse approval event:', e)
              }
              break
            }
            case 'metadata': {
              try {
                streamedMetadata = JSON.parse(event.data)
                if (currentAssistantMsg) {
                  currentAssistantMsg.agentMetadata = streamedMetadata
                }
              } catch (e) {
                console.error('Failed to parse metadata:', e)
              }
              break
            }
            case 'error': {
              typingAnimator.flush()
              const errorContent = `错误: ${event.data}`
              if (currentAssistantMsg) {
                currentAssistantMsg.content = errorContent
              } else {
                currentMessages.push({
                  id: `assistant-${Date.now()}-error`,
                  role: 'assistant',
                  content: errorContent,
                  timestamp: Date.now(),
                })
              }
              break
            }
          }
        },
        sessionId.value,
        currentDemo.value,
        userId.value
      )

      // 等待打字机动画完成
      if (currentAssistantMsg) {
        await typingAnimator.waitComplete()
        currentAssistantMsg.content = currentContent.trim()
        if (streamedMetadata) {
          currentAssistantMsg.agentMetadata = streamedMetadata
        }
        // 清理空内容的助手消息（仅当没有工具调用时）
        // 如果有工具调用但文本为空，保留消息并显示占位符
        if (!currentAssistantMsg.content) {
          const hasToolCalls = currentMessages.some(m => m.role === 'tool' || m.role === 'approval')
          if (hasToolCalls) {
            // 有工具调用但没有文本，显示占位符
            currentAssistantMsg.content = '已执行操作'
          } else {
            // 既没有工具调用也没有文本，删除消息
            const idx = currentMessages.indexOf(currentAssistantMsg)
            if (idx !== -1) currentMessages.splice(idx, 1)
          }
        }
      }

    } catch (error) {
      typingAnimator.flush()
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
      // 消息完成后刷新会话列表（新会话会出现在列表中）
      loadSessionList()
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

  async function editMessage(messageId: string, msgIndex: number, newContent: string) {
    const currentMessages = demoMessages.value.get(currentDemo.value)
    if (!currentMessages) return

    // 调用后端截断 checkpoint（删除该消息及之后的所有消息）
    await editMessageApi(sessionId.value, currentDemo.value, msgIndex)

    // 前端截断：移除该消息及之后的所有消息
    currentMessages.splice(msgIndex)

    // 用编辑后的内容重新发送
    await sendMessageAndReceive(newContent)
  }

  function switchDemo(demoId: string) {
    const demo = demos.value.find(d => d.id === demoId)
    if (!demo || demo.coming_soon) {
      return false
    }

    typingAnimator.flush()
    // 切换 demo（历史会自动切换，因为 messages 是计算属性）
    currentDemo.value = demoId
    return true
  }

  async function submitApproval(approvalMsgId: string, decision: 'approve' | 'reject', rejectMessage = '') {
    const currentMessages = demoMessages.value.get(currentDemo.value)
    if (!currentMessages) return

    // 找到审批消息并更新状态
    const approvalMsg = currentMessages.find(m => m.id === approvalMsgId)
    if (!approvalMsg || !approvalMsg.approvalInfo) return

    approvalMsg.approvalInfo.status = decision === 'approve' ? 'approved' : 'rejected'

    isLoading.value = true

    // 流式处理状态
    let currentAssistantMsg: Message | null = null
    let currentContent = ''
    let streamedMetadata: AgentMetadata | undefined
    let assistantMsgCount = 0

    const ensureAssistantMsg = () => {
      if (!currentAssistantMsg) {
        assistantMsgCount++
        currentMessages.push({
          id: `assistant-${Date.now()}-${assistantMsgCount}`,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
        })
        currentAssistantMsg = currentMessages[currentMessages.length - 1]
      }
    }

    const decisions = approvalMsg.approvalInfo.actions.map(() => ({
      type: decision,
      message: decision === 'reject' ? (rejectMessage || '用户拒绝了此操作') : '',
    }))

    try {
      await sendApprovalStream(
        decisions,
        (event: SSEEvent) => {
          switch (event.event) {
            case 'message': {
              currentContent += event.data
              ensureAssistantMsg()
              typingAnimator.update(currentAssistantMsg!, currentContent)
              break
            }
            case 'tool_call': {
              typingAnimator.reset()
              if (currentAssistantMsg) {
                currentAssistantMsg.content = currentContent.trim()
                currentAssistantMsg = null
                currentContent = ''
              }
              try {
                const eventData = JSON.parse(event.data)

                // 如果tool调用来自sub-agent，将内容作为assistant消息显示
                const isSubAgent = eventData.tool_name === 'coder-agent' || eventData.tool_name === 'sre-agent'

                if (isSubAgent && eventData.output) {
                  // Sub-agent响应作为assistant消息
                  assistantMsgCount++
                  const assistantMsg: Message = {
                    id: `assistant-${Date.now()}-${assistantMsgCount}`,
                    role: 'assistant',
                    content: eventData.output,
                    timestamp: Date.now(),
                  }
                  currentMessages.push(assistantMsg)
                } else {
                  // 普通工具调用，显示为工具消息
                  const toolMsg: Message = {
                    id: `tool-${Date.now()}-${assistantMsgCount}`,
                    role: 'tool',
                    content: eventData.output,
                    timestamp: Date.now(),
                    toolInfo: { toolName: eventData.tool_name, status: eventData.status }
                  }
                  currentMessages.push(toolMsg)
                }
              } catch (e) {
                console.error('Failed to parse tool_call event:', e)
              }
              break
            }
            case 'approval': {
              typingAnimator.reset()
              if (currentAssistantMsg) {
                currentAssistantMsg.content = currentContent.trim()
                currentAssistantMsg = null
                currentContent = ''
              }
              try {
                const eventData = JSON.parse(event.data)
                const newApprovalMsg: Message = {
                  id: `approval-${Date.now()}`,
                  role: 'approval',
                  content: eventData.actions.map((a: any) =>
                    `${a.name}: ${JSON.stringify(a.args)}`
                  ).join('\n'),
                  timestamp: Date.now(),
                  approvalInfo: {
                    actions: eventData.actions,
                    timestamp: eventData.timestamp,
                    status: 'pending',
                  }
                }
                currentMessages.push(newApprovalMsg)
              } catch (e) {
                console.error('Failed to parse approval event:', e)
              }
              break
            }
            case 'metadata': {
              try {
                streamedMetadata = JSON.parse(event.data)
                if (currentAssistantMsg) {
                  currentAssistantMsg.agentMetadata = streamedMetadata
                }
              } catch (e) {
                console.error('Failed to parse metadata:', e)
              }
              break
            }
            case 'error': {
              typingAnimator.flush()
              const errorContent = `错误: ${event.data}`
              if (currentAssistantMsg) {
                currentAssistantMsg.content = errorContent
              } else {
                currentMessages.push({
                  id: `assistant-${Date.now()}-error`,
                  role: 'assistant',
                  content: errorContent,
                  timestamp: Date.now(),
                })
              }
              break
            }
          }
        },
        sessionId.value,
        currentDemo.value,
        userId.value
      )

      if (currentAssistantMsg) {
        await typingAnimator.waitComplete()
        currentAssistantMsg.content = currentContent.trim()
        if (streamedMetadata) {
          currentAssistantMsg.agentMetadata = streamedMetadata
        }
        // 清理空内容的助手消息（仅当没有工具调用时）
        // 如果有工具调用但文本为空，保留消息并显示占位符
        if (!currentAssistantMsg.content) {
          const hasToolCalls = currentMessages.some(m => m.role === 'tool' || m.role === 'approval')
          if (hasToolCalls) {
            // 有工具调用但没有文本，显示占位符
            currentAssistantMsg.content = '已执行操作'
          } else {
            // 既没有工具调用也没有文本，删除消息
            const idx = currentMessages.indexOf(currentAssistantMsg)
            if (idx !== -1) currentMessages.splice(idx, 1)
          }
        }
      }
    } catch (error) {
      typingAnimator.flush()
      const errorMsg = `错误: ${error instanceof Error ? error.message : '未知错误'}`
      currentMessages.push({
        id: `assistant-${Date.now()}-error`,
        role: 'assistant',
        content: errorMsg,
        timestamp: Date.now(),
      })
    } finally {
      isLoading.value = false
    }
  }

  // 历史会话列表
  const sessionList = ref<ChatSession[]>([])

  async function loadSessionList() {
    try {
      sessionList.value = await getSessions(currentDemo.value)
      console.log(`[ChatStore] 加载会话列表: ${sessionList.value.length} 个`)
    } catch (error) {
      console.error('Failed to load session list:', error)
    }
  }

  function switchSession(targetSessionId: string) {
    if (targetSessionId === sessionId.value) return

    typingAnimator.flush()
    sessionId.value = targetSessionId
    // 清空当前消息，由 loadHistory 重新加载
    demoMessages.value.set(currentDemo.value, [])
    loadHistory()
    console.log('[ChatStore] 切换会话:', targetSessionId)
  }

  async function startNewChat() {
    const newSessionId = `session-${Date.now()}`
    sessionId.value = newSessionId
    demoMessages.value.set(currentDemo.value, [])
    // 刷新会话列表
    await loadSessionList()
    console.log('[ChatStore] 开始新聊天:', newSessionId)
  }

  async function deleteSession(targetSessionId: string) {
    try {
      await deleteSessionApi(targetSessionId, currentDemo.value)
      // 如果删除的是当前活跃会话，切换到新聊天
      if (targetSessionId === sessionId.value) {
        await startNewChat()
      }
      // 刷新会话列表
      await loadSessionList()
      console.log('[ChatStore] 删除会话:', targetSessionId)
    } catch (error) {
      console.error('Failed to delete session:', error)
      throw error
    }
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
    demoMessages,
    sessionList,
    loadDemos,
    loadHistory,
    loadSessionList,
    sendMessageAndReceive,
    editMessage,
    submitApproval,
    clearHistory,
    switchDemo,
    switchSession,
    startNewChat,
    deleteSession,
    registerScrollCallback,
  }
})
