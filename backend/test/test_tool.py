from datetime import datetime

from langchain.tools import tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate


@tool
def get_current_date():
    """获取今天的日期"""
    return datetime.now().strftime("%Y-%m-%d")

from model import zhipu_model as model

def chat_with_tool():
    all_tools = {"get_current_date": get_current_date}
    question = "今天是几月几号"
    final_messages = [question]
    model_with_tool = model.bind_tools(all_tools.values())
    first_answer = model_with_tool.invoke(question)
    final_messages.append(first_answer)
    for tool_call in first_answer.tool_calls:
        select_tool = all_tools[tool_call["name"]]
        print(select_tool)
        tool_call_result = select_tool.invoke(tool_call)
        print(tool_call_result)
        final_messages.append(tool_call_result)
    print(model_with_tool.invoke(final_messages))

def agent_with_tool():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的助手。"),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(model, [get_current_date], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[get_current_date], verbose=True)

    print(agent_executor.invoke({
        "input": "今天是几月几号"
    }))

if __name__ == '__main__':
    # chat_with_tool()
    agent_with_tool()