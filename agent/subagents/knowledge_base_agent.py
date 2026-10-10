"""RAGFlow 知识库子智能体：检索企业内部文档。"""

from agent.prompts import sub_agents_content
from tools.ragflow_tools import create_ask_delete, get_assistant_list

_config = sub_agents_content["ragflow"]

knowledge_base_agent = {
    "name": _config["name"],
    "description": _config["description"],
    "system_prompt": _config["system_prompt"],
    "tools": [get_assistant_list, create_ask_delete],
}