import os
from typing import Annotated, List

from dotenv import load_dotenv
from langchain_core.tools import tool
from mysql.connector import Error, connect

from api.monitor import monitor

load_dotenv()


def get_db_config():
    """从环境变量读取 MySQL 连接配置，返回可直接传给 connect() 的字典。"""
    config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "collation": os.getenv("MYSQL_COLLATION", "utf8mb4_unicode_ci"),
        "autocommit": True,
        "sql_mode": os.getenv("MYSQL_SQL_MODE", "TRADITIONAL"),
        # 强制使用纯 Python 实现连接：
        # Windows 上 C 扩展(_mysql_connector) 在连接 MySQL 8 时，
        # caching_sha2_password 认证 + 非 SSL 场景下会抛笼统的
        # RuntimeError: Failed raising error.，use_pure=True 可绕过该问题。
        "use_pure": True
    }
    # 移除空值
    config = {k: v for k, v in config.items() if v is not None}
    # 校验核心配置是否存在
    required_keys = ["host", "user", "password", "database"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"缺少数据库配置项：{','.join(missing_keys)}")
    return config


@tool
def list_sql_tables() -> Annotated[List[str], "列出数据库中所有表名"]:
    """列出当前配置的 MySQL 数据库中所有可用的表。

    执行 SQL 之前先调用本工具，确认有哪些表以及准确的表名。
    成功返回表名列表，配置缺失或执行异常时返回可读的错误信息。
    """
    monitor.report_tool("数据库查询表名工具")
    config = get_db_config()
    try:
        if not all(k in config for k in ["user", "password", "database"]):
            return "错误:数据库配置缺失"
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                table_names = [row[0] for row in cursor.fetchall()]
                return f"数据库中可用表名：{table_names}"
            
    except Error as e:
        return f"列出数据表失败：{str(e)}"


@tool
def get_table_data(table_name: Annotated[str, "要读取数据的表名"]) -> Annotated[str, "表的前 100 行数据（CSV 格式）"]:
    """读取指定表的前 100 行，用于快速预览字段与数据形态。

    返回 CSV 文本：第一行为列名，之后每行一条记录，字段以英文逗号分隔。
    """
    monitor.report_tool("数据库内容浏览工具")
    config = get_db_config()
    try:
        if not all(k in config for k in ["user", "password", "database"]):
            return "错误:数据库配置缺失"
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                if cursor.description is None:
                    return f"表 {table_name} 为空"
                column_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                csv_data = f"{','.join(column_names)}\n"
                for row in rows:
                    csv_data += f"{','.join(map(str, row))}\n"
                return csv_data  
    except Error as e:
        return f"查询表{table_name}数据失败：{str(e)}"


@tool
def execute_sql_query(sql_query: Annotated[str, "要执行的SQL 查询语句"]) -> Annotated[str, "查询结果或成功消息"]:
    """执行自定义 SQL 查询，返回 CSV 格式结果。

    适用于筛选、联表、聚合等复杂查询，字段同样以英文逗号分隔。
    """
    monitor.report_tool("数据库SQL查询工具")
    config = get_db_config()
    try:
        if not all(k in config for k in ["user", "password", "database"]):
            return "错误:数据库配置缺失"
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                if cursor.description is None:
                    return f"查询结果为空"
                column_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                if not rows:
                    return f"查询成功,查询数据为空"
                csv_data = f"{','.join(column_names)}\n"
                for row in rows:
                    csv_data += f"{','.join(map(str, row))}\n"
                return csv_data  
    except Error as e:
        return f"执行SQL{sql_query}失败：{str(e)}"


    
if __name__ == "__main__":
    #测试工具函数
    result = execute_sql_query("SELECT * FROM drugs")
    print(result)
