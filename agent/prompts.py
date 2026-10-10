"""加载 prompt/prompts.yml，供主智能体与子智能体使用。"""

from pathlib import Path

import yaml


def load_yaml(file_path):
    """读取 YAML 配置文件，返回其对应的字典。"""
    # 使用 safe_load 避免反序列化时执行任意对象构造
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


project_root_path = Path(__file__).parents[1]
yaml_file_path = project_root_path / "prompt" / "prompts.yml"

prompt_yaml_content = load_yaml(yaml_file_path)

main_agent_content = prompt_yaml_content["main_agent"]
sub_agents_content = prompt_yaml_content["sub_agents"]