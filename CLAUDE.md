# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **LangChain Learning Project** that explores LLM framework concepts through building a ChatGPT-style chat application. The project uses a **Monorepo structure** with Vue frontend and FastAPI backend, implementing various LangChain demos to learn the framework systematically.

**Learning Philosophy:** Demo-Driven Learning - each LangChain concept is practiced through a dedicated demo.

## Project Structure

```
langchain-demo/
├── frontend/          # Vue 3 + TypeScript + Element Plus
│   ├── src/
│   │   ├── api/      # API 调用层
│   │   ├── stores/   # Pinia 状态管理
│   │   ├── views/    # 页面组件
│   │   ├── router/   # Vue Router 配置
│   │   └── main.ts   # 入口文件
│   └── package.json
│
├── backend/           # FastAPI + LangChain 后端
│   ├── demos/        # 各个 Demo 实现
│   │   └── basic_chat.py       # 基础 LLM 问答
│   ├── common/       # 通用配置
│   │   └── config.py
│   ├── models/       # LLM 模型初始化
│   │   └── __init__.py
│   ├── main.py       # FastAPI 主应用
│   └── pyproject.toml
│
└── docs/             # 学习文档
```

## Development Commands

### Backend (FastAPI + LangChain)

```bash
cd backend

# Install dependencies
uv sync

# Run development server (with auto-reload)
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Run without auto-reload
uv run uvicorn main:app --port 8000
```

### Frontend (Vue 3 + Element Plus)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Tech Stack

### Frontend
- **Framework:** Vue 3.5+ with Composition API
- **Language:** TypeScript
- **UI Library:** Element Plus
- **State Management:** Pinia
- **Routing:** Vue Router 4
- **Build Tool:** Vite 6
- **Markdown:** markdown-it + highlight.js

### Backend
- **Framework:** FastAPI
- **LLM Framework:** LangChain 0.3+
- **LLM Provider:** 智谱 AI (GLM-4-Flash)
- **Package Manager:** uv
- **Python:** 3.13+

## Architecture

### Backend Directory Structure

```
backend/
├── main.py           # FastAPI 主应用入口
├── model.py          # 模型配置
├── test/             # ⚠️ 所有测试文件必须放在此目录
├── demos/            # 各个 Demo 实现
├── common/           # 通用配置
├── models/           # LLM 模型初始化
├── agents/           # Agent 配置
└── skills/           # Skills 定义
```

**⚠️ 重要：测试文件规范**
- 所有测试脚本（`test_*.py`）必须生成在 `backend/test/` 目录下
- 不要在 backend 根目录创建测试文件
- 测试文件命名格式：`test_<功能描述>.py`

### Model Configuration (`backend/models/__init__.py`)

Centralized LLM client creation:

- `get_zhipu_model()` - 智谱 AI GLM-4-Flash (default)
- `get_openrouter_model()` - OpenRouter (for alternative models)

**Custom Implementation:**
- `ZhipuChatModel` - Custom BaseChatModel that correctly handles Zhipu's API Key format (`id.secret`)

### Demo Architecture (`backend/demos/`)

Each demo is a self-contained module implementing a specific LangChain concept:

1. **basic_chat.py** - Basic LLM Chat
   - Direct model invocation
   - Conversation history management
   - Streaming response support

### FastAPI Endpoints (`backend/main.py`)

- `GET /health` - Health check
- `GET /api/demos` - List available demos
- `POST /api/chat` - Non-streaming chat
- `POST /api/chat/stream` - Streaming chat
- `POST /api/chat/clear` - Clear conversation history

### Frontend Components (`frontend/src/`)

- `ChatView.vue` - Main chat interface (ChatGPT style)
- `stores/chat.ts` - Pinia store for chat state
- `api/chat.ts` - API client with streaming support

## Environment Variables

Required in `.env` (backend root):

```bash
# 智谱 AI API
ZHIPU_API_KEY=your_api_key_here

# LangSmith Tracing (可选)
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=langchain-learning
LANGSMITH_API_KEY=your_langsmith_key
```

## Learning Path

### Phase 1: Foundation ✅
- [x] Project setup (Vue + FastAPI)
- [x] Basic LLM chat (GLM-4-Flash)
- [x] Streaming responses
- [x] Conversation history

### Phase 2: RAG & Retrieval (Planned)
- [ ] Document upload and processing
- [ ] Vector embeddings and storage
- [ ] Retrieval-Augmented Generation
- [ ] Multi-document chat

### Phase 3: Agents (Planned)
- [ ] Tool calling fundamentals
- [ ] ReAct Agent pattern
- [ ] Custom tools definition
- [ ] Agent orchestration

### Phase 4: Advanced Features (Planned)
- [ ] Multi-turn conversation strategies
- [ ] Memory management
- [ ] Chain composition
- [ ] LangGraph workflows

## Development Workflow

1. **Learn a concept** - Study LangChain documentation
2. **Create a demo** - Implement in `backend/demos/`
3. **Integrate to UI** - Add to frontend demo list
4. **Test thoroughly** - Verify functionality
5. **Document learnings** - Update docs/ notes

## Common Issues

### Backend Issues

**Problem:** 401 InvalidApiKey
- **Solution:** Verify ZHIPU_API_KEY in `.env` is correct

**Problem:** Module not found
- **Solution:** Run `uv sync` in backend directory

### Frontend Issues

**Problem:** vite: command not found
- **Solution:** Run `npm install` in frontend directory

**Problem:** CORS errors
- **Solution:** Check backend CORS origins in `common/config.py`

## Code Style

- **Python:** Follow PEP 8, use type hints
- **TypeScript:** Strict mode enabled
- **Vue:** Composition API with `<script setup>`
- **API:** RESTful design with appropriate HTTP methods

## Testing

### Backend Tests
```bash
cd backend
# Health check
curl http://localhost:8000/health

# Test chat API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'
```

### Frontend Tests
Open browser to http://localhost:5174 and verify:
- Chat interface loads
- Demo list displays correctly
- Messages send and receive properly
- Streaming responses work
