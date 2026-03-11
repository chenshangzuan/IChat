from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

from model import zhipu_model as model

def chat_with_template():
    # 示例 prompt
    prompt = ChatPromptTemplate.from_template("Explain {topic} in a simple sentence")

    # 构建链
    chain = prompt | model

    # 调用
    response = chain.invoke({"topic": "LangChain 与 OpenRouter 集成"})
    print(response)

def chat_chain_with_history():
    # 示例 prompt
    prompt = ChatPromptTemplate.from_template("Explain {topic} in a simple sentence")

    # 构建链
    chain = prompt | model

    runnable = RunnableWithMessageHistory(
        chain,
        get_session_history=get_in_memory_history
    )
    runnable.invoke("你好")

def model_chat1():
    chat1 = model.invoke("你是谁")
    print(chat1)

def model_chat1_with_history():
    history = InMemoryChatMessageHistory()
    model.bind(history=history)
    chat1 = model.invoke("你是谁")
    print(chat1.content)
    chat2 = model.invoke("重复一次")
    print(chat2.content)

def model_chat2():
    chat_messages = [
        SystemMessage("你是个中英文翻译"),
        HumanMessage("你好，最近过得怎么样？")
    ]
    print(model.invoke(chat_messages))

def model_chat3():
    print(model.invoke({"role": "user", "content": "你好，最近过得怎么样？"}))

def get_in_memory_history():
    return InMemoryChatMessageHistory()

if __name__ == '__main__':
    model_chat1()
    pass
