from pathlib import Path

from langchain_core.tools import tool

from api.context import get_session_context
from api.monitor import monitor
from utils.path_utils import resolve_path

try:
    from typing import Annotated
except ImportError:  # Python < 3.9
    from typing_extensions import Annotated


@tool
def generate_markdown(
        content: Annotated[str, "要写入Markdown文档的文本内容"],
        filename: Annotated[str, "Markdown文档的文件名（不包含扩展名或包含.md）"],
        path: Annotated[str, "文件保存的绝对路径"] = ""
):
    """根据提供的文本内容，生成对应的 Markdown(.md) 文件。"""
    monitor.report_tool("Markdown文档生成工具", {"写入的文本内容": content})
    if not filename.endswith('.md'):
        filename += '.md'

    # 结合当前会话的工作目录解析最终落盘位置
    session_dir = get_session_context()
    if path and path != ".":
        full_input_path = str(Path(path) / filename)
    else:
        full_input_path = filename
    file_path = Path(resolve_path(full_input_path, session_dir))

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"[MarkdownTool] 已写入: {file_path}")
        return f"Markdown文件 '{file_path}' 已成功生成并保存。"
    except Exception as e:
        print(f"[MarkdownTool] 写入失败: {e}")
        return f"生成Markdown文件失败: {str(e)}"