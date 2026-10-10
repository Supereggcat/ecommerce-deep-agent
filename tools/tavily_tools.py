import os
import time
from typing import Literal

from dotenv import load_dotenv
from langchain_core.tools import tool
from requests.exceptions import ConnectionError as RequestsConnectionError
from tavily import TavilyClient

from api.monitor import monitor

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False
    ) -> dict | str:
    """联网检索公开信息，返回适配大模型的结构化结果。

    当需要外部公开信息、行业动态、最新新闻等时效性数据时使用。

    query: 搜索关键词，例如 "2026年电商行业增长趋势"
    max_results: 返回结果条数，建议不超过 5
    topic: 内容类型，可选 general / news / finance
    include_raw_content: 是否返回网页原文，False 为摘要版，True 为详细版

    返回 Tavily 的结构化结果（含 query 与 results，results 中每项包含 url、content 等）。
    """
    monitor.report_tool(tool_name="internet_search",
                        args={"query": query, "max_results": max_results,
                              "topic": topic, "include_raw_content": include_raw_content})

    # 网络抖动（如远端重置连接）时自动重试，避免单次失败中断整个任务
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return tavily_client.search(query=query, max_results=max_results, topic=topic,
                                        include_raw_content=include_raw_content)
        except RequestsConnectionError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    