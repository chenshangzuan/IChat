"""
模型模块
提供统一的 LLM 模型初始化
"""
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from common.config import config
import httpx
import json
from typing import Any, List, Optional, Sequence, Union


def get_openrouter_model(model: str = "openai/gpt-oss-20b:free", temperature: float = 0.7):
    """
    获取 OpenRouter 模型

    Args:
        model: 模型名称
        temperature: 温度参数

    Returns:
        ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=model,
        api_key=config.OPENROUTER_API_KEY,
        base_url=config.OPENROUTER_BASE_URL,
        temperature=temperature,
    )


class ZhipuChatModel(BaseChatModel):
    """智谱 AI 自定义 ChatModel，正确处理 id.secret 格式的 API Key"""

    model: str = "glm-4.5-air"
    temperature: float = 0.7
    api_key: str = ""
    _bound_tools: Optional[List[dict]] = None

    def __init__(self, model: str = "glm-4", temperature: float = 0.7, api_key: str = ""):
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or config.ZHIPU_API_KEY
        self._bound_tools = None

    def bind_tools(
        self,
        tools: Sequence[Union[dict[str, Any], type, BaseTool, callable]],
        *,
        tool_choice: Optional[Union[str, dict, bool]] = None,
        **kwargs: Any,
    ) -> "ZhipuChatModel":
        """
        绑定工具到模型（用于 Deep Agents 子代理调用）

        Args:
            tools: 工具列表
            tool_choice: 工具选择策略
            **kwargs: 其他参数

        Returns:
            绑定工具后的模型实例
        """
        # 转换工具为 OpenAI 格式
        formatted_tools = []
        for tool in tools:
            if isinstance(tool, dict):
                formatted_tools.append(tool)
            elif isinstance(tool, BaseTool):
                formatted_tools.append(convert_to_openai_tool(tool))
            elif callable(tool):
                # 对于 callable，尝试转换为工具格式
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or "",
                        "parameters": {}
                    }
                })

        # 创建新实例并保存绑定的工具
        new_model = ZhipuChatModel(
            model=self.model,
            temperature=self.temperature,
            api_key=self.api_key
        )
        new_model._bound_tools = formatted_tools
        return new_model

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成（不推荐使用）"""
        raise NotImplementedError("请使用异步方法")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成响应"""

        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if msg.type == "human":
                formatted_messages.append({"role": "user", "content": msg.content})
            elif msg.type == "ai":
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif msg.type == "system":
                formatted_messages.append({"role": "system", "content": msg.content})
            elif msg.type == "tool":
                # 处理工具消息
                formatted_messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": getattr(msg, "tool_call_id", "")
                })

        # 构建请求体
        request_body = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
        }

        # 如果有绑定的工具，添加到请求中
        if self._bound_tools:
            request_body["tools"] = self._bound_tools

        request_body.update(kwargs)

        # 调用智谱 API（使用异步客户端）
        async with httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0),
        ) as client:
            response = await client.post(
                # "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions",
                json=request_body,
            )

            response.raise_for_status()
            data = response.json()

            # 解析响应
            message_data = data["choices"][0]["message"]
            content = message_data.get("content", "")

            # 处理工具调用 - 将 tool_calls 转换为 LangChain 格式
            tool_calls_data = message_data.get("tool_calls", None)
            tool_calls_list = []

            if tool_calls_data:
                from langchain_core.messages.tool import ToolCall
                import json

                for tc in tool_calls_data:
                    function = tc.get("function", {})
                    args_str = function.get("arguments", "{}")

                    # 尝试将 JSON 字符串解析为字典
                    try:
                        args_dict = json.loads(args_str)
                    except:
                        args_dict = {}

                    tool_call = ToolCall(
                        name=function.get("name", ""),
                        args=args_dict,  # 使用解析后的字典
                        id=tc.get("id", "")
                    )
                    tool_calls_list.append(tool_call)

                # 创建带工具调用信息的 AIMessage
                ai_message = AIMessage(
                    content=content or "",
                    tool_calls=tool_calls_list
                )
            else:
                ai_message = AIMessage(content=content)

            return ChatResult(
                generations=[ChatGeneration(message=ai_message)]
            )

    @property
    def _llm_type(self) -> str:
        return "zhipu-chat"


def get_zhipu_model(model: str = "glm-4.7", temperature: float = 0.7):
    """
    获取智谱 AI 模型

    Args:
        model: 模型名称（默认 glm-4.5-air，也可使用 glm-4-plus, glm-4-air, glm-4-flash 等）
        temperature: 温度参数

    Returns:
        ZhipuChatModel 实例
    """
    return ZhipuChatModel(model=model, temperature=temperature, api_key=config.ZHIPU_API_KEY)


# 默认模型（使用智谱 AI GLM-4）
default_llm = get_zhipu_model()
