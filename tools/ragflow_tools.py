from langchain_core.tools import tool
from ragflow_sdk import RAGFlow

from api.monitor import monitor
from utils.ragflow_config import load_ragflow_env

api_key, base_url = load_ragflow_env()
ragflow_client = RAGFlow(api_key=api_key, base_url=base_url)


@tool
def get_assistant_list() -> str:
    """查询 RAGFlow 上可用的聊天助手及其关联的知识库。

    向某个助手提问前，必须先调用本工具确认助手的名称与能力范围。
    返回每行一个助手：助手名称 / 功能介绍 / 关联的知识库；
    没有可用助手或查询异常时返回相应的提示信息。
    """
    monitor.report_tool(tool_name="ragflow聊天助手列表查询工具：get_assistant_list")

    try:
        chat_list = ragflow_client.list_chats()
        if not chat_list:
            return "没有任何可用助手"

        chat_info = ""
        for chat in chat_list:
            dataset_names = []
            dataset_list = chat.datasets  # 该助手关联的知识库
            if dataset_list and isinstance(dataset_list, list):
                for dataset in dataset_list:
                    dataset_names.append(dataset['name'])

            chat_info += (
                f"助手名称:{chat.name};功能介绍：{chat.description}; "
                f"关联的知识库：{'、'.join(dataset_names)} \n"
            )
        return chat_info
    except Exception as e:
        return f"查询助手信息异常，无可用助手,异常信息:{str(e)}"

@tool
def create_ask_delete(chat_name, question) -> str:
    """向指定助手提问一次（创建会话 → 提问 → 关闭会话）。

    调用前必须先用 get_assistant_list 确认助手名称。
    chat_name: 助手名称；question: 本次提问的问题。
    """
    monitor.report_tool(
        tool_name="ragflow提问助手工具：create_ask_delete",
        args={"chat_name": chat_name, "question": question},
    )

    try:
        chats = ragflow_client.list_chats(name=chat_name)
        use_chat = chats[0]

        session = use_chat.create_session(name="temp_session_ask")
        response = session.ask(question=question, stream=True)

        result = ""
        for part in response:
            result = part.content

        use_chat.delete_sessions(ids=[session.id])
        return result
    except Exception as e:
        return f"提问失败，错误原因：{str(e)}"