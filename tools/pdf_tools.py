import logging
from pathlib import Path

from langchain_core.tools import tool

from api.context import get_session_context
from api.monitor import monitor
from utils.path_utils import resolve_path
from utils.word_converter import convert_md_to_pdf_via_word

try:
    from typing import Annotated, Optional
except ImportError:  # Python < 3.9
    from typing_extensions import Annotated, Optional


@tool
def convert_md_to_pdf(
        md_filename: Annotated[str, "要转换的Markdown文档路径（包含.md后缀）"],
        pdf_filename: Annotated[Optional[str], "输出的PDF文件路径（可选，默认与源文件同名）"] = None
) -> str:
    """
    将 Markdown 文档转换为 PDF（基于 Microsoft Word 引擎）。
    仅负责路径解析，实际转换逻辑在 utils/word_converter.py。
    """
    monitor.report_tool("Markdown转PDF工具")

    try:
        session_dir = get_session_context()
        md_abs_path = Path(resolve_path(str(Path(md_filename).with_suffix('.md')), session_dir))

        if not md_abs_path.exists():
            return f"错误：文件不存在 {md_abs_path}"

        if pdf_filename:
            pdf_abs_path = Path(resolve_path(str(Path(pdf_filename).with_suffix('.pdf')), session_dir))
        else:
            pdf_abs_path = md_abs_path.with_suffix('.pdf')

        return convert_md_to_pdf_via_word(md_abs_path, pdf_abs_path)

    except Exception as e:
        logging.error(f"转换失败: {e}", exc_info=True)
        return f"转换失败: {str(e)}"