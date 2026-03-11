from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatZhipuAI
from dotenv import load_dotenv
import os

load_dotenv()

# 读取环境变量
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = os.getenv("OPENROUTER_BASE_URL")
zhipu_key = os.getenv("ZHIPU_API_KEY")

# 创建 LangChain LLM 实例，指向 OpenRouter
openrouter_model = ChatOpenAI(
    api_key=openrouter_key,
    base_url=openrouter_url,
    model="openai/gpt-oss-20b:free",  # 选一个免费的模型
    temperature=0.7
)

zhipu_model = ChatZhipuAI(
    api_key=zhipu_key,
    model="glm-4.5-flash"
)