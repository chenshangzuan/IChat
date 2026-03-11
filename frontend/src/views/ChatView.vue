<template>
  <div class="chat-view">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>LangChain 学习</h2>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleNewChat"
          circle
          size="small"
        />
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

    <!-- 主聊天区域 -->
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
import { ref, onMounted, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { AgentMetadata } from '@/api/chat'
import {
  Plus,
  ChatDotRound,
  User,
  Service,
  Position,
  Right,
  Tools,
  Clock,
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()

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

async function handleSend() {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isLoading) return

  inputMessage.value = ''
  await chatStore.sendMessageAndReceive(message)
  scrollToBottom()
}

function handleNewChat() {
  chatStore.clearHistory()
}

function handleSelectDemo(demoId: string) {
  chatStore.switchDemo(demoId)
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
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

.sidebar {
  width: 260px;
  background: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #ddd;
}

.sidebar-header {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #34495e;
}

.sidebar-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.demo-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.demo-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.demo-item:hover {
  background: #34495e;
}

.demo-item.active {
  background: #3498db;
}

.demo-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.demo-name {
  font-weight: 500;
}

.demo-description {
  font-size: 12px;
  color: #95a5a6;
  margin: 0;
}

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
  background: #409eff;
  color: white;
}

.message.assistant .message-avatar {
  background: #67c23a;
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
  background: #409eff;
  color: white;
}

.message.assistant .message-text {
  background: #f0f0f0;
}

.message-text :deep(pre) {
  background: #1e1e1e;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.message-text :deep(code) {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
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
  background: #909399;
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
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #409eff;
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
</style>
