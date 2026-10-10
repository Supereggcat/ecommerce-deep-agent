"""网络搜索子智能体：检索公开的互联网信息。"""

from agent.prompts import sub_agents_content
from tools.tavily_tools import internet_search

_config = sub_agents_content["tavily"]

network_search_agent = {
    "name": _config["name"],
    "description": _config["description"],
    "system_prompt": _config["system_prompt"],
    "tools": [internet_search],
}