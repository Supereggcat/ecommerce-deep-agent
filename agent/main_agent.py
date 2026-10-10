import shutil
from pathlib import Path

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

from agent.llm import model
from agent.prompts import main_agent_content
from agent.subagents.database_query_agent import database_query_agent
from agent.subagents.knowledge_base_agent import knowledge_base_agent
from agent.subagents.network_search_agent import network_search_agent
from api.context import reset_session_context, set_session_context, set_thread_context
from api.monitor import monitor
from tools.markdown_tools import generate_markdown
from tools.pdf_tools import convert_md_to_pdf
from tools.upload_file_read_tool import read_file_content


main_agent = create_deep_agent(
    model=model,
    system_prompt=main_agent_content["system_prompt"],
    subagents=[knowledge_base_agent, database_query_agent, network_search_agent],
    checkpointer=InMemorySaver(),
    tools=[generate_markdown, convert_md_to_pdf, read_file_content],
)

project_root_path = Path(__file__).parents[1]


async def run_deep_agent(task_query: str, session_id: str):
    """流式执行主智能体，并把执行过程与最终结果实时推送给前端。

    task_query: 前端提问
    session_id: 前端会话标识，用于隔离 ContextVars 并创建该会话独立的 output 目录
    """
    print(f"当前会话的 main_agent 开始执行，会话 id: {session_id}")
    # 该会话的专属工作目录：output/session_<id>
    session_dir = project_root_path / "output" / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)
    # 路径统一用 POSIX 风格；给大模型的只是相对项目根目录的路径
    session_dir_str = session_dir.as_posix()
    relative_session_dir_str = session_dir.relative_to(project_root_path).as_posix()

    # 把该会话上传的文件复制到工作目录，并提示模型优先读取
    updated_dir_path = project_root_path / "updated" / f"session_{session_id}"
    updated_info_prompt = ""
    files = []
    if updated_dir_path.exists():
        files = [f.name for f in updated_dir_path.iterdir() if f.is_file()]
    if files:
        for filename in files:
            # copy2 会保留原文件的修改时间等元数据
            shutil.copy2(updated_dir_path / filename, session_dir / filename)
        updated_info_prompt = (
            f"\n    [已上传文件] 已加载到工作目录:\n"
            + "\n".join([f"    - {f}" for f in files])
            + "\n    请优先使用工具（read_file_content）读取并参考这些文件。"
        )

    # 写入 ContextVars：工具据此拿到工作目录，monitor 据 thread_id 把消息推给对应前端
    session_dir_token = set_session_context(session_dir_str)
    session_id_token = set_thread_context(session_id)
    monitor.report_session_dir(session_dir_str)

    #执行主智能体
    config = {
        "configurable":{
            "thread_id":session_id
        }
    }

    # 把工作目录约定拼进用户消息，让模型把新文件都写进该会话目录
    path_instruction = f"""
    【工作环境指令】
    工作目录: {relative_session_dir_str}
    {updated_info_prompt}

    规则：
    1. 新生成文件必须保存到工作目录：'{relative_session_dir_str}/filename'
    2. 读取已上传的文件时，请直接将文件名（例如：'商品清单.xlsx'）作为 filename 参数传入（read_file_content）读取工具，不要带上任何目录前缀。
    3. 使用相对路径，禁止使用绝对路径
    4. 若存在上传文件，请先分析内容
    """
    # 用 try/except 兜住模型侧的异常，避免单次任务失败拖垮整个服务
    try:
        async for chunk in main_agent.astream(
            {"messages": [{"role": "user", "content": task_query + path_instruction}]},
            config=config,
        ):
            # 解析流式结果：只关心 model 节点产出的最新消息
            for node_name, state in chunk.items():
                if not state or "messages" not in state:
                    continue
                messages = state["messages"]
                if not messages or not isinstance(messages, list):
                    continue
                last_message = messages[-1]
                if node_name != "model":
                    continue

                if last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        # 子智能体调用：task 工具的 args 为 {subagent_type, description}
                        if tool_call["name"] == "task":
                            monitor.report_assistant(
                                assistant_name=tool_call["args"]["subagent_type"],
                                args={"description": tool_call["args"]["description"]},
                            )
                        else:
                            monitor.report_assistant(
                                assistant_name=tool_call["name"],
                                args=tool_call["args"],
                            )
                elif last_message.content:
                    print(f"主智能体执行最终结果: {last_message.content[:100]}")
                    monitor.report_task_result(last_message.content)
    except Exception as e:
        monitor._emit("error", f"主智能体执行异常: {str(e)}")
    finally:
        # 清理上下文，避免污染后续请求
        reset_session_context(session_dir_token, session_id_token)