import os
from typing import Optional, Tuple

from dotenv import load_dotenv


def load_ragflow_env() -> Tuple[Optional[str], Optional[str]]:
    """读取 RAGFlow 连接配置。

    优先加载项目根目录下的 .env，找不到时回退到系统环境变量。
    返回 (api_key, base_url)，缺失时为 None。
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    return os.getenv("RAGFLOW_API_KEY"), os.getenv("RAGFLOW_API_URL")
