import os

from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model

# 递归向上查找 .env，保证在任意工作目录下启动都能读到配置
load_dotenv(find_dotenv())

# DeepSeek 使用 OpenAI 兼容接口，无需额外安装 langchain-deepseek。
# 支持通过 .env 或系统环境变量覆盖：
#   DEEPSEEK_API_KEY  必填
#   DEEPSEEK_MODEL    默认 deepseek-chat
#   DEEPSEEK_BASE_URL 默认 https://api.deepseek.com
model = init_chat_model(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    model_provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)