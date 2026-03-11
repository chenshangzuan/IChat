# LangChain 学习项目

一个通过实践学习 LangChain 框架的项目，构建 ChatGPT 风格的聊天应用，通过不同的 Demo 掌握 LangChain 的核心概念。

## 🎯 项目特点

- **Demo 驱动学习** - 每个 LangChain 概念都通过实际的 Demo 来掌握
- **ChatGPT 风格界面** - 美观易用的聊天界面
- **流式响应** - 实时打字机效果
- **对话历史** - 支持多轮对话
- **渐进式学习路径** - 从基础到高级，系统化学习

## 🏗️ 技术栈

### 前端
- Vue 3 + TypeScript
- Element Plus UI 组件库
- Pinia 状态管理
- Vue Router 路由
- Vite 构建工具
- Markdown 渲染 + 代码高亮

### 后端
- FastAPI 框架
- LangChain 0.3+
- 智谱 AI GLM-4-Flash
- Python 3.13+
- uv 包管理器

## 🚀 快速开始

### 1. 安装依赖

```bash
# 后端依赖
cd backend
uv sync

# 前端依赖
cd frontend
npm install
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
ZHIPU_API_KEY=你的智谱API密钥
```

获取智谱 API Key：https://open.bigmodel.cn/

### 3. 启动服务

**终端 1 - 启动后端：**
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

**终端 2 - 启动前端：**
```bash
cd frontend
npm run dev
```

### 4. 访问应用

- **前端地址：** http://localhost:5174
- **后端 API：** http://localhost:8000
- **API 文档：** http://localhost:8000/docs

## 📁 项目结构

```
langchain-demo/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/         # API 调用
│   │   ├── stores/      # Pinia 状态管理
│   │   ├── views/       # 页面组件
│   │   └── router/      # 路由配置
│   └── package.json
│
├── backend/              # FastAPI 后端
│   ├── demos/           # LangChain Demos
│   │   └── basic_chat.py    # 基础 LLM 问答 ✅
│   ├── common/          # 通用配置
│   ├── models/          # LLM 模型配置
│   └── main.py          # FastAPI 主应用
│
├── docs/                # 学习文档
├── CLAUDE.md            # AI 编程指南
└── README.md            # 本文件
```

## 📚 学习路径

### ✅ Phase 1: 基础（已完成）
- [x] 项目初始化（Vue + FastAPI）
- [x] 基础 LLM 问答
- [x] 流式响应
- [x] 对话历史管理

### 📝 Phase 2: RAG & 检索（计划中）
- [ ] 文档上传和处理
- [ ] 向量化和存储
- [ ] 检索增强生成（RAG）
- [ ] 多文档问答

### 🤖 Phase 3: Agents（计划中）
- [ ] Tool Calling 基础
- [ ] ReAct Agent 模式
- [ ] 自定义工具
- [ ] Agent 编排

### 🚀 Phase 4: 高级特性（计划中）
- [ ] 多轮对话策略
- [ ] Memory 管理
- [ ] Chain 组合
- [ ] LangGraph 工作流

## 🎨 功能特性

### 已实现
- ✅ ChatGPT 风格聊天界面
- ✅ Demo 切换功能
- ✅ 流式响应显示
- ✅ Markdown 渲染
- ✅ 代码语法高亮
- ✅ 对话历史
- ✅ 智谱 AI GLM-4 模型集成

### 规划中
- ⏳ 文档上传（PDF、Word、Markdown）
- ⏳ RAG 问答
- ⏳ Agent 对话
- ⏳ 多模型切换
- ⏳ 对话导出

## 🔧 开发指南

详细的开发指南请参阅 [CLAUDE.md](./CLAUDE.md)

### 测试 API

```bash
# 健康检查
curl http://localhost:8000/health

# 测试聊天
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'
```

## 📖 学习资源

- [LangChain 官方文档](https://python.langchain.com/)
- [智谱 AI 开放平台](https://open.bigmodel.cn/)
- [Vue 3 文档](https://vuejs.org/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Element Plus 文档](https://element-plus.org/)

## 🐛 常见问题

### 后端启动失败
- 检查 API Key 是否正确配置
- 确认已运行 `uv sync`

### 前端启动失败
- 确认已运行 `npm install`
- 检查端口 5174 是否被占用

### API 调用 401 错误
- 验证 `.env` 中的 `ZHIPU_API_KEY`
- 确认 API Key 格式正确

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Happy Learning with LangChain! 🚀**
