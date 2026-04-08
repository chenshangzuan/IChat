<template>
  <div class="chat-view">
    <!-- 左侧：Demo 列表（主目录） -->
    <aside class="demo-list-sidebar">
      <div class="sidebar-header">
        <h2>
          <img src="@/assets/ai_bot_transparent.png" class="title-icon" alt="AI Bot" />
          IChat
        </h2>
      </div>
      <div class="demo-list">
        <div
          v-for="demo in chatStore.demos"
          :key="demo.id"
          class="demo-item"
          :class="{ active: chatStore.currentDemo === demo.id }"
          @click="handleSelectDemo(demo.id)"
        >
          <div class="demo-info">
            <span class="demo-name">{{ demo.name }}</span>
            <el-tag v-if="demo.coming_soon" size="small" type="info">即将推出</el-tag>
          </div>
          <p class="demo-description">{{ demo.description }}</p>
        </div>
      </div>
    </aside>

    <!-- 中间：聊天侧边栏（二级） - 仅 deepagents 显示 -->
    <aside class="chat-sidebar" :class="{ collapsed: !chatSidebarExpanded }" v-if="chatStore.currentDemo === 'deepagents'">
      <!-- 新聊天 -->
      <div class="new-chat-item" @click="handleNewChat">
        <el-icon :size="18">
          <Edit />
        </el-icon>
        <span>新聊天</span>
      </div>

      <!-- 历史聊天列表（占位） -->
      <div class="history-section" v-if="showHistory">
        <div class="section-header" @click="toggleHistory">
          <div class="section-title">
            <el-icon :size="18"><Clock /></el-icon>
            <span>历史聊天</span>
          </div>
          <el-icon :class="{ 'rotated': historyExpanded }">
            <ArrowDown />
          </el-icon>
        </div>
        <div v-if="historyExpanded" class="history-list">
          <div class="history-empty">
            <el-icon><Clock /></el-icon>
            <span>即将推出</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- 二级侧边栏切换按钮 -->
    <div
      v-if="chatStore.currentDemo === 'deepagents'"
      class="sidebar-toggle"
      @click="toggleChatSidebar"
    >
      <el-icon :size="16">
        <ArrowLeft v-if="chatSidebarExpanded" />
        <ArrowRight v-else />
      </el-icon>
    </div>

    <!-- 右侧：主聊天区域 -->
    <main class="chat-main">
      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!chatStore.hasMessages" class="empty-state">
          <img src="@/assets/ai.png" class="empty-icon" alt="AI" />
          <h3>与 AI 一起，重新定义创造</h3>
        </div>

        <div v-else class="messages">
          <div
            v-for="message in chatStore.messages"
            :key="message.id"
            class="message"
            :class="message.role"
          >
            <!-- 工具消息渲染（作为独立消息单元） -->
            <template v-if="message.role === 'tool'">
              <div class="message-avatar tool-avatar">
                <el-icon :size="20">
                  <Tools />
                </el-icon>
              </div>
              <div class="message-content">
                <div class="tool-call-card">
                  <div class="tool-card-header">
                    <span class="tool-icon-text">{{ getToolIcon(message.toolInfo?.toolName) }}</span>
                    <span class="tool-card-name">{{ formatToolName(message.toolInfo?.toolName) }}</span>
                    <el-tag size="small" :type="getToolStatusType(message.toolInfo?.status)">
                      {{ message.toolInfo?.status === 'completed' ? '完成' : message.toolInfo?.status }}
                    </el-tag>
                    <el-icon class="expand-icon" :class="{ expanded: isToolExpanded(message.id) }" @click="toggleToolExpand(message.id)">
                      <ArrowDown />
                    </el-icon>
                  </div>
                  <div class="tool-card-output" v-show="isToolExpanded(message.id)">
                    <pre>{{ message.content }}</pre>
                  </div>
                </div>
              </div>
            </template>

            <!-- 审批消息渲染 -->
            <template v-else-if="message.role === 'approval'">
              <div class="message-avatar approval-avatar">
                <el-icon :size="20">
                  <Edit />
                </el-icon>
              </div>
              <div class="message-content">
                <div class="approval-card">
                  <div class="approval-header">
                    <span class="approval-icon">&#9888;&#65039;</span>
                    <span class="approval-title">文件写入审批</span>
                    <el-tag
                      size="small"
                      :type="message.approvalInfo?.status === 'pending' ? 'warning' : message.approvalInfo?.status === 'approved' ? 'success' : 'danger'"
                    >
                      {{ message.approvalInfo?.status === 'pending' ? '待审批' : message.approvalInfo?.status === 'approved' ? '已批准' : '已拒绝' }}
                    </el-tag>
                  </div>
                  <div class="approval-actions-list">
                    <div
                      v-for="(action, idx) in message.approvalInfo?.actions"
                      :key="idx"
                      class="approval-action-item"
                    >
                      <div class="approval-action-name">{{ action.name }}</div>
                      <div class="approval-action-args">
                        <div v-if="action.args?.file_path" class="approval-file-path">
                          {{ action.args.file_path }}
                        </div>
                        <div v-if="action.args?.content" class="approval-content-preview">
                          <pre>{{ (action.args.content || '').substring(0, 500) }}{{ (action.args.content || '').length > 500 ? '...' : '' }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-if="message.approvalInfo?.status === 'pending'" class="approval-buttons">
                    <el-button
                      type="success"
                      size="small"
                      @click="handleApproval(message.id, 'approve')"
                      :loading="chatStore.isLoading"
                    >
                      批准
                    </el-button>
                    <el-button
                      type="danger"
                      size="small"
                      @click="handleApproval(message.id, 'reject')"
                      :loading="chatStore.isLoading"
                    >
                      拒绝
                    </el-button>
                  </div>
                </div>
              </div>
            </template>

            <!-- 用户/助手消息渲染 -->
            <template v-else>
              <div class="message-avatar">
                <el-icon v-if="message.role === 'user'" :size="20">
                  <User />
                </el-icon>
                <el-icon v-else :size="20">
                  <Service />
                </el-icon>
              </div>
              <div class="message-content">
                <!-- Agent 徽章和元数据（仅 deepagents demo） -->
                <div v-if="message.role === 'assistant' && message.agentMetadata" class="agent-metadata">
                  <el-tag :type="getAgentTagType(message.agentMetadata.agent_type)" size="small">
                    {{ getAgentIcon(message.agentMetadata.agent_type) }} {{ getAgentName(message.agentMetadata.agent_type) }}
                  </el-tag>
                  <div class="agent-stats">
                    <el-tooltip content="委托次数" placement="top">
                      <span class="stat-item">
                        <el-icon><Right /></el-icon>
                        {{ message.agentMetadata.delegations }}
                      </span>
                    </el-tooltip>
                    <el-tooltip content="工具调用" placement="top">
                      <span class="stat-item">
                        <el-icon><Tools /></el-icon>
                        {{ message.agentMetadata.tool_calls }}
                      </span>
                    </el-tooltip>
                    <el-tooltip content="Skill 调用" placement="top">
                      <span class="stat-item">
                        <el-icon><MagicStick /></el-icon>
                        {{ message.agentMetadata.skill_calls }}
                      </span>
                    </el-tooltip>
                    <el-tooltip v-if="message.agentMetadata.skills && message.agentMetadata.skills.length > 0" :content="`使用的 Skills: ${message.agentMetadata.skills.join(', ')}`" placement="top">
                      <span class="stat-item skills-badge">
                        {{ message.agentMetadata.skills.map(s => getSkillIcon(s)).join(' ') }}
                      </span>
                    </el-tooltip>
                    <el-tooltip content="耗时" placement="top">
                      <span class="stat-item">
                        <el-icon><Clock /></el-icon>
                        {{ message.agentMetadata.duration.toFixed(2) }}s
                      </span>
                    </el-tooltip>
                  </div>
                </div>

                <div class="message-text" v-html="renderMarkdown(message.content)"></div>
                <div class="message-time">
                  {{ formatTime(message.timestamp) }}
                </div>
              </div>
            </template>
          </div>

          <!-- 加载中指示器 -->
          <div v-if="chatStore.isLoading" class="message assistant loading">
            <div class="message-avatar">
              <el-icon :size="20">
                <Service />
              </el-icon>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-container">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入消息..."
            @keydown.enter.exact="handleSend"
            @keydown.enter.shift.prevent
            :disabled="chatStore.isLoading"
          />
          <div class="input-actions">
            <div class="actions-left">
              <el-dropdown
                v-if="currentPresetQuestions.length > 0"
                trigger="click"
                @command="handlePresetQuestion"
              >
                <el-button circle :icon="QuestionFilled" class="action-btn" title="预设问题" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="question in currentPresetQuestions"
                      :key="question"
                      :command="question"
                    >
                      {{ question }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-popover
                :visible="showUserIdPopover"
                placement="top"
                :width="240"
                trigger="click"
              >
                <template #reference>
                  <el-button
                    circle
                    :icon="User"
                    class="action-btn"
                    :class="{ 'user-id-active': chatStore.userId }"
                    :title="chatStore.userId ? `当前用户: ${chatStore.userId}` : '设置用户 ID'"
                    @click="showUserIdPopover = !showUserIdPopover"
                  />
                </template>
                <div class="user-id-popover">
                  <div style="margin-bottom: 8px; font-size: 13px; color: #666;">设置用户 ID</div>
                  <el-input
                    v-model="userIdInput"
                    placeholder="输入用户 ID"
                    size="small"
                    clearable
                    @keydown.enter="confirmUserId"
                  />
                  <div style="margin-top: 8px; text-align: right;">
                    <el-button size="small" @click="showUserIdPopover = false">取消</el-button>
                    <el-button size="small" type="primary" @click="confirmUserId">确认</el-button>
                  </div>
                </div>
              </el-popover>
            </div>
            <div class="actions-right">
              <el-button
                type="primary"
                :icon="Position"
                circle
                @click="handleSend"
                :disabled="!inputMessage.trim() || chatStore.isLoading"
                class="send-btn"
                title="发送消息"
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { AgentMetadata } from '@/api/chat'
import {
  ChatDotRound,
  User,
  Service,
  Position,
  Right,
  Tools,
  Clock,
  QuestionFilled,
  MagicStick,
  Edit,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()

// User ID 弹出框状态
const showUserIdPopover = ref(false)
const userIdInput = ref(chatStore.userId)

function confirmUserId() {
  chatStore.setUserId(userIdInput.value.trim())
  showUserIdPopover.value = false
}

// 审批处理
async function handleApproval(msgId: string, decision: 'approve' | 'reject') {
  await chatStore.submitApproval(msgId, decision)
  scrollToBottom()
}

// 历史聊天列表状态
const showHistory = ref(true)
const historyExpanded = ref(false)

// 二级侧边栏展开状态
const chatSidebarExpanded = ref(true)

// 每个 demo 的预设问题
const presetQuestionsMap: Record<string, string[]> = {
  'deepagents': [
    '你现在有哪些skills',
    '帮我写一个Python快速排序算法',
    '如何分析 Nginx 日志中的 502 错误？',
    '如何部署一个 FastAPI 服务到生产环境？',
    '帮我把这个接口描述规范化：query ai gateway list',
    '帮我把这个接口操作符规范化：zec:elasticIp:listNetworkTypes',
    '帮我写一首关于元旦节的诗，然后存到/memories/ 目录下',
    '查看/memories/ 目录下有哪些文件',
  ],
  'basic-chat': [
    '什么是 LangChain？',
    'LLM 是如何工作的？',
    '什么是 Prompt Engineering？',
    '什么是 RAG（检索增强生成）？',
    '介绍一下 AI Agent 的概念',
  ],
}

// 当前 demo 的预设问题
const currentPresetQuestions = computed(() => {
  return presetQuestionsMap[chatStore.currentDemo] || []
})

const md = new MarkdownIt({
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  },
})

function renderMarkdown(content: string): string {
  return md.render(content)
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getAgentIcon(agentType?: string): string {
  const icons: Record<string, string> = {
    'orchestrator': '🎯',
    'coder': '👨‍💻',
    'sre': '🔧',
  }
  return icons[agentType || 'orchestrator'] || '🎯'
}

function getAgentName(agentType?: string): string {
  const names: Record<string, string> = {
    'orchestrator': 'Orchestrator',
    'coder': 'Coder Agent',
    'sre': 'SRE Agent',
  }
  return names[agentType || 'orchestrator'] || 'Orchestrator'
}

function getAgentTagType(agentType?: string): string {
  const types: Record<string, string> = {
    'orchestrator': 'primary',
    'coder': 'success',
    'sre': 'warning',
  }
  return types[agentType || 'orchestrator'] || 'primary'
}

function getSkillIcon(skillName: string): string {
  const icons: Record<string, string> = {
    // Coder skills
    'code-generation': '✨',
    'code-optimization': '⚡',
    'code-review': '🔍',
    // SRE skills
    'log-analysis': '📊',
    'deployment': '🚀',
    'sql-audit': '🗄️',
    'audit-log-normalization': '📋',
    'sre-operations': '🔧',
  }
  return icons[skillName] || '🎨'
}

// 工具消息展开状态（默认全部展开）
const expandedTools = ref<Set<string>>(new Set())

// 检查工具是否展开（默认展开）
function isToolExpanded(toolId: string): boolean {
  // 如果还没有记录，默认为展开
  if (!expandedTools.value.has(toolId) && !expandedTools.value.has(`collapsed-${toolId}`)) {
    return true
  }
  // 如果有记录，按记录的状态
  return expandedTools.value.has(toolId)
}

function toggleToolExpand(toolId: string) {
  if (isToolExpanded(toolId)) {
    // 当前展开，切换为折叠
    expandedTools.value.delete(toolId)
    expandedTools.value.add(`collapsed-${toolId}`)
  } else {
    // 当前折叠，切换为展开
    expandedTools.value.delete(`collapsed-${toolId}`)
    expandedTools.value.add(toolId)
  }
}

function getToolIcon(toolName?: string): string {
  const icons: Record<string, string> = {
    'coder-agent': '👨‍💻',
    'sre-agent': '🔧',
    'file_manager': '📁',
    'memory_search': '🧠',
    'task': '🔄',
    'python_repl': '🐍',
    'shell': '💻',
  }
  return icons[toolName || ''] || '⚙️'
}

function formatToolName(toolName?: string): string {
  if (!toolName) return '工具调用'
  return toolName
}

function getToolStatusType(status?: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const types: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    'completed': 'success',
    'initiated': 'info',
    'failed': 'danger',
  }
  return types[status || ''] || 'info'
}

async function handleSend() {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isLoading) return

  inputMessage.value = ''
  await chatStore.sendMessageAndReceive(message)
  scrollToBottom()
}

function handleNewChat() {
  chatStore.startNewChat()
  inputMessage.value = ''
}

function handleSelectDemo(demoId: string) {
  chatStore.switchDemo(demoId)
}

function handlePresetQuestion(question: string) {
  inputMessage.value = question
}

function toggleHistory() {
  historyExpanded.value = !historyExpanded.value
}

function toggleChatSidebar() {
  chatSidebarExpanded.value = !chatSidebarExpanded.value
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  chatStore.loadDemos()
})
</script>

<style scoped>
.chat-view {
  position: relative;
  display: flex;
  height: 100vh;
  background: #F5F3FF;
}

/* 左侧 Demo 列表（主目录） */
.demo-list-sidebar {
  width: 200px;
  background: #F5F3FF;
  color: #0F172A;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #EDE9FE;
}

.demo-list-sidebar .sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #EDE9FE;
}

.demo-list-sidebar .sidebar-header h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.demo-list-sidebar .title-icon {
  width: 30px;
  height: 30px;
  object-fit: contain;
}

.demo-list-sidebar .demo-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.demo-list-sidebar .demo-item {
  padding: 10px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.demo-list-sidebar .demo-item:hover {
  background: #EDE9FE;
}

.demo-list-sidebar .demo-item.active {
  background: #7C3AED;
  color: #FFFFFF;
}

.demo-list-sidebar .demo-item.active .demo-name {
  color: #FFFFFF;
}

.demo-list-sidebar .demo-item.active .demo-description {
  color: rgba(255, 255, 255, 0.9);
}

.demo-list-sidebar .demo-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.demo-list-sidebar .demo-name {
  font-weight: 500;
  font-size: 14px;
}

.demo-list-sidebar .demo-description {
  font-size: 11px;
  color: #475569;
  margin: 0;
  line-height: 1.3;
}

/* 中间聊天侧边栏（二级） */
.chat-sidebar {
  width: 240px;
  min-width: 240px;
  max-width: 240px;
  background: #EDE9FE;
  color: #0F172A;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #DDD6FE;
  transition: all 0.3s ease;
  overflow: hidden;
}

.chat-sidebar.collapsed {
  width: 56px;
  min-width: 56px;
  max-width: 56px;
}

/* 收起时隐藏文字 */
.chat-sidebar.collapsed .new-chat-item span,
.chat-sidebar.collapsed .section-header span {
  opacity: 0;
  visibility: hidden;
  width: 0;
  overflow: hidden;
}

/* 收起时图标居中 */
.chat-sidebar.collapsed .new-chat-item,
.chat-sidebar.collapsed .section-header {
  padding: 14px 0;
  justify-content: center !important;
  display: flex;
}

.chat-sidebar.collapsed .new-chat-item {
  gap: 0;
}

.chat-sidebar.collapsed .section-header {
  padding: 14px 0;
}

.chat-sidebar.collapsed .section-header .section-title {
  justify-content: center;
  width: 100%;
  margin: 0;
}

.chat-sidebar.collapsed .section-header .el-icon {
  margin: 0;
}

/* 收起时隐藏历史聊天的展开箭头 */
.chat-sidebar.collapsed .section-header > .el-icon:last-child {
  display: none;
}

/* 收起时 section-title 占满宽度并居中图标 */
.chat-sidebar.collapsed .section-header .section-title {
  width: 100%;
  justify-content: center;
  margin: 0;
  padding: 0;
}

.chat-sidebar.collapsed .section-header .section-title span {
  display: none;
}

/* 二级侧边栏切换按钮 */
.sidebar-toggle {
  position: absolute;
  left: 440px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: #EDE9FE;
  border: 1px solid #DDD6FE;
  border-left: none;
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: left 0.3s ease, background 0.2s ease;
  color: #7C3AED;
}

.sidebar-toggle:hover {
  background: #DDD6FE;
}

.sidebar-toggle:active {
  transform: translateY(-50%) scale(0.95);
}

/* 当侧边栏收起时，按钮移到左侧 */
.chat-view:has(.chat-sidebar.collapsed) .sidebar-toggle {
  left: 256px;
}

.chat-sidebar .sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #E0E7FF;
}

/* 新聊天项 - 文字链接样式 */
.new-chat-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
  color: #0F172A;
  font-size: 14px;
  font-weight: 500;
}

.new-chat-item span {
  transition: opacity 0.2s ease, visibility 0.2s ease, width 0.2s ease;
  white-space: nowrap;
}

.new-chat-item:hover {
  background: rgba(221, 214, 254, 0.7);
}

.new-chat-item .el-icon {
  width: 18px;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
}

/* 历史聊天区域 */
.history-section {
  flex: 1;
  overflow-y: auto;
}

.history-section .section-header {
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.history-section .section-header .section-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.history-section .section-header .section-title .el-icon {
  width: 18px;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.history-section .section-header span {
  transition: opacity 0.2s ease, visibility 0.2s ease;
  white-space: nowrap;
}

.history-section .section-header:hover {
  background: rgba(221, 214, 254, 0.7);
}

.section-header .el-icon {
  transition: transform 0.3s;
}

.section-header .el-icon.rotated {
  transform: rotate(180deg);
}

.history-list {
  padding: 8px;
}

.history-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 16px;
  color: #64748B;
  font-size: 13px;
}

/* 右侧主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-icon {
  width: 120px;
  height: 120px;
  object-fit: contain;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 500;
  color: #64748B;
  margin-top: 16px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.messages {
  max-width: 800px;
  margin: 0 auto;
}

.message {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #7C3AED;
  color: white;
}

.message.assistant .message-avatar {
  background: #A78BFA;
  color: white;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f0f0f0;
  line-height: 1.6;
}

.message.user .message-text {
  background: #7C3AED;
  color: white;
}

.message.assistant .message-text {
  background: #F5F3FF;
  padding: 16px 20px;
  border: 1px solid #EDE9FE;
}

/* 工具消息样式 */
.message.tool {
  margin-bottom: 12px;
}

.tool-call-container {
  max-width: 70%;
  margin-left: 48px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  overflow: hidden;
  font-size: 14px;
}

.tool-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: #FFFFFF;
  border-bottom: 1px solid #E2E8F0;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
}

.tool-header:hover {
  background: #F1F5F9;
}

.tool-icon {
  font-size: 18px;
  margin-right: 10px;
}

.tool-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-name {
  font-weight: 500;
  font-size: 14px;
  color: #334155;
}

.expand-icon {
  transition: transform 0.3s;
  color: #94A3B8;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.tool-output {
  padding: 12px 14px;
  max-height: 300px;
  overflow-y: auto;
  background: #FAFBFC;
}

.tool-output pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  color: #475569;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.message-text :deep(pre) {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  border: 1px solid #e1e4e8;
  margin: 12px 0;
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #24292f;
}

.message-text :deep(code) {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  color: #24292f;
}

/* 列表样式 */
.message-text :deep(ol),
.message-text :deep(ul) {
  padding-left: 24px;
  margin: 8px 0;
}

.message-text :deep(li) {
  margin: 4px 0;
  line-height: 1.6;
}

/* 代码块内的列表 */
.message-text :deep(pre ol),
.message-text :deep(pre ul) {
  margin: 8px 0;
  padding-left: 28px;
}

.message-text :deep(pre li) {
  margin: 4px 0;
}

/* 行内代码样式 */
.message-text :deep(p code),
.message-text :deep(li code) {
  background: #f6f8fa;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #e1e4e8;
  font-size: 13px;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.message.loading .message-text {
  display: none;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #f0f0f0;
  border-radius: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #A78BFA;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 输入区域样式 */
.input-area {
  max-width: 800px;
  margin: 0 auto 20px;
  width: 100%;
  padding: 0 20px;
}

.input-container {
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(124, 58, 237, 0.08);
  border: 1px solid #EDE9FE;
  overflow: hidden;
}

.input-area .el-textarea {
  flex: 1;
}

/* 输入框样式 */
.input-area :deep(.el-textarea__inner) {
  border: none;
  background: transparent;
  padding: 16px 20px;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  box-shadow: none;
  border-radius: 0;
}

.input-area :deep(.el-textarea__inner:focus) {
  background: transparent;
  box-shadow: none;
  outline: none;
}

.input-area :deep(.el-textarea__inner::placeholder) {
  color: #A78BFA;
}

/* 输入框底部操作栏 */
.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: transparent;
}

.actions-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.actions-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 操作按钮通用样式 */
.input-actions .action-btn {
  background: transparent;
  border: none;
  color: #7C3AED;
  transition: all 0.2s ease;
}

.input-actions .action-btn:hover {
  background: #F5F3FF;
  color: #6D28D9;
}

.input-actions .action-btn.user-id-active {
  color: #fff;
  background: #7C3AED;
}

/* 发送按钮样式 */
.input-actions .send-btn {
  background: #7C3AED;
  border-color: #7C3AED;
  color: white;
  transition: all 0.2s ease;
}

.input-actions .send-btn:hover {
  background: #6D28D9;
  transform: scale(1.05);
}

.input-actions .send-btn:disabled {
  background: #EDE9FE;
  border-color: #EDE9FE;
  color: #A78BFA;
  transform: none;
}

/* Agent 元数据样式 */
.agent-metadata {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #F5F3FF;
  border-radius: 8px;
  border-left: 3px solid #7C3AED;
}

.agent-stats {
  display: flex;
  gap: 16px;
  margin-left: auto;
}

/* 工具消息样式（作为独立消息单元） */
.message.tool {
  margin-bottom: 16px;
}

.message.tool .tool-avatar {
  background: #F0FDF4;
  color: #16A34A;
}

.message.tool .message-content {
  padding: 0;
  background: transparent;
  border: none;
}

.tool-call-card {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.tool-call-card:hover {
  border-color: #CBD5E1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.tool-card-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #FFFFFF;
  gap: 10px;
}

.tool-icon-text {
  font-size: 20px;
}

.tool-card-name {
  font-weight: 600;
  font-size: 14px;
  color: #1E293B;
  flex: 1;
}

.tool-card-header .expand-icon {
  transition: transform 0.3s;
  color: #94A3B8;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.tool-card-header .expand-icon:hover {
  color: #64748B;
  background: #F1F5F9;
}

.tool-card-header .expand-icon.expanded {
  transform: rotate(180deg);
}

.tool-card-output {
  padding: 16px;
  background: #FAFBFC;
  border-top: 1px solid #E2E8F0;
}

.tool-card-output pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: #475569;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
}

.message.approval {
  margin-bottom: 16px;
}

.message.approval .message-content {
  padding: 0;
  background: transparent;
  border: none;
}

/* 审批消息样式 */
.approval-avatar {
  background: #FEF3C7 !important;
  color: #D97706 !important;
}

.approval-card {
  border: 1px solid #FDE68A;
  border-radius: 12px;
  overflow: hidden;
  background: #FFFBEB;
}

.approval-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #FEF3C7;
}

.approval-icon {
  font-size: 16px;
}

.approval-title {
  font-weight: 600;
  font-size: 14px;
  color: #92400E;
  flex: 1;
}

.approval-actions-list {
  padding: 12px 16px;
}

.approval-action-item {
  margin-bottom: 8px;
}

.approval-action-name {
  font-weight: 600;
  font-size: 13px;
  color: #78350F;
  margin-bottom: 4px;
}

.approval-file-path {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #B45309;
  background: #FEF3C7;
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 4px;
}

.approval-content-preview pre {
  margin: 4px 0 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #475569;
  background: #F8FAFC;
  padding: 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #E2E8F0;
}

.approval-buttons {
  padding: 8px 16px 12px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.stat-item .el-icon {
  font-size: 14px;
}

.skills-badge {
  font-size: 14px;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  margin-left: 4px;
}
</style>
