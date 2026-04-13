"""
模型模块
提供统一的 LLM 模型初始化
"""
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from common.config import config
import httpx
import json
from typing import Any, AsyncIterator, List, Optional, Sequence, Union


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

    def _format_messages(self, messages: List[BaseMessage]) -> list[dict]:
        """将 LangChain 消息列表转换为智谱 API 格式"""
        formatted = []
        for msg in messages:
            if msg.type == "human":
                formatted.append({"role": "user", "content": msg.content})
            elif msg.type == "ai":
                formatted.append({"role": "assistant", "content": msg.content})
            elif msg.type == "system":
                formatted.append({"role": "system", "content": msg.content})
            elif msg.type == "tool":
                formatted.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": getattr(msg, "tool_call_id", "")
                })
        return formatted

    def _build_request_body(self, formatted_messages: list[dict], **kwargs) -> dict:
        """构建 API 请求体"""
        request_body = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
        }
        if self._bound_tools:
            request_body["tools"] = self._bound_tools
        request_body.update(kwargs)
        return request_body

    @property
    def _api_url(self) -> str:
        return "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成响应（非流式）"""
        formatted_messages = self._format_messages(messages)
        request_body = self._build_request_body(formatted_messages, **kwargs)

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0),
        ) as client:
            response = await client.post(self._api_url, json=request_body)
            response.raise_for_status()
            data = response.json()

        # 解析响应
        message_data = data["choices"][0]["message"]
        content = message_data.get("content", "")

        # 处理工具调用
        tool_calls_data = message_data.get("tool_calls", None)
        tool_calls_list = []

        if tool_calls_data:
            from langchain_core.messages.tool import ToolCall

            for tc in tool_calls_data:
                function = tc.get("function", {})
                args_str = function.get("arguments", "{}")
                try:
                    args_dict = json.loads(args_str)
                except Exception:
                    args_dict = {}

                tool_call = ToolCall(
                    name=function.get("name", ""),
                    args=args_dict,
                    id=tc.get("id", "")
                )
                tool_calls_list.append(tool_call)

            ai_message = AIMessage(content=content or "", tool_calls=tool_calls_list)
        else:
            ai_message = AIMessage(content=content)

        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """流式生成响应 - 逐 token yield"""
        from langchain_core.messages import AIMessageChunk
        from langchain_core.messages.tool import ToolCallChunk
        from langchain_core.outputs import ChatGenerationChunk

        formatted_messages = self._format_messages(messages)
        request_body = self._build_request_body(formatted_messages, stream=True, **kwargs)

        # tool_calls 流式累积
        tc_name_buffer = ""  # 累积 function name
        tc_args_buffer = ""  # 累积 function arguments
        tc_id_buffer = ""    # 累积 tool_call id
        in_tool_call = False

        async with httpx.AsyncClient(
            headers=self._headers,
            timeout=httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0),
        ) as client:
            async with client.stream("POST", self._api_url, json=request_body) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue

                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        # 流结束，如果还有未 yield 的 tool_call，先发出去
                        if in_tool_call and tc_name_buffer:
                            try:
                                args_dict = json.loads(tc_args_buffer) if tc_args_buffer else {}
                            except Exception:
                                args_dict = {}
                            tool_call_chunk = ToolCallChunk(
                                name=tc_name_buffer,
                                args=json.dumps(args_dict, ensure_ascii=False),
                                id=tc_id_buffer,
                                index=0,
                            )
                            yield ChatGenerationChunk(
                                message=AIMessageChunk(content="", tool_call_chunks=[tool_call_chunk])
                            )
                        break

                    try:
                        chunk_data = json.loads(data_str)
                    except Exception:
                        continue

                    choices = chunk_data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})

                    # 处理文本内容
                    content = delta.get("content", "")
                    if content:
                        yield ChatGenerationChunk(
                            message=AIMessageChunk(content=content)
                        )

                    # 处理 tool_calls（流式中分多个 chunk 到达）
                    tool_calls_delta = delta.get("tool_calls")
                    if tool_calls_delta:
                        for tc_delta in tool_calls_delta:
                            # 新 tool_call 开始（有 id 和 function.name）
                            tc_id = tc_delta.get("id", "")
                            if tc_id:
                                # 如果之前有未完成的 tool_call，先 yield
                                if in_tool_call and tc_name_buffer:
                                    try:
                                        args_dict = json.loads(tc_args_buffer) if tc_args_buffer else {}
                                    except Exception:
                                        args_dict = {}
                                    tool_call_chunk = ToolCallChunk(
                                        name=tc_name_buffer,
                                        args=json.dumps(args_dict, ensure_ascii=False),
                                        id=tc_id_buffer,
                                        index=0,
                                    )
                                    yield ChatGenerationChunk(
                                        message=AIMessageChunk(content="", tool_call_chunks=[tool_call_chunk])
                                    )
                                    tc_name_buffer = ""
                                    tc_args_buffer = ""

                                tc_id_buffer = tc_id
                                in_tool_call = True

                            function = tc_delta.get("function", {})
                            name_part = function.get("name", "")
                            args_part = function.get("arguments", "")

                            if name_part:
                                tc_name_buffer += name_part
                            if args_part:
                                tc_args_buffer += args_part

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
