<template>
  <div class="chat-view">
    <!-- 左侧：Demo 列表（主目录） -->
    <aside class="demo-list-sidebar">
      <div class="sidebar-header">
        <h2>
          <el-icon :size="18" class="title-icon">
            <ChatDotRound />
          </el-icon>
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
          <span>历史聊天</span>
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
          <el-icon :size="64" color="#909399">
            <ChatDotRound />
          </el-icon>
          <h3>开始对话</h3>
          <p>选择一个 demo，然后输入消息开始聊天</p>
        </div>

        <div v-else class="messages">
          <div
            v-for="message in chatStore.messages"
            :key="message.id"
            class="message"
            :class="message.role"
          >
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
                  <el-tooltip v-if="message.agentMetadata.skills.length > 0" :content="`使用的 Skills: ${message.agentMetadata.skills.join(', ')}`" placement="top">
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
        <el-dropdown
          v-if="currentPresetQuestions.length > 0"
          trigger="click"
          @command="handlePresetQuestion"
        >
          <el-button circle :icon="QuestionFilled" title="预设问题" />
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
        <el-button
          type="primary"
          :icon="Position"
          @click="handleSend"
          :disabled="!inputMessage.trim() || chatStore.isLoading"
          circle
        />
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
  color: #7C3AED;
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
  justify-content: center;
}

.chat-sidebar.collapsed .new-chat-item {
  gap: 0;
}

.chat-sidebar.collapsed .section-header {
  padding: 14px 0;
}

.chat-sidebar.collapsed .section-header .el-icon {
  margin: 0;
}

/* 收起时隐藏历史聊天的展开箭头 */
.chat-sidebar.collapsed .section-header > .el-icon:last-child {
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
  flex-shrink: 0;
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

.empty-state h3 {
  margin: 16px 0 8px;
  font-weight: 500;
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

.input-area {
  display: flex;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #eee;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.input-area .el-textarea {
  flex: 1;
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
