"""数据库查询子智能体：读取业务库的表结构与数据。"""

from agent.prompts import sub_agents_content
from tools.db_tools import execute_sql_query, get_table_data, list_sql_tables

_config = sub_agents_content["db"]

database_query_agent = {
    "name": _config["name"],
    "description": _config["description"],
    "system_prompt": _config["system_prompt"],
    "tools": [list_sql_tables, get_table_data, execute_sql_query],
}