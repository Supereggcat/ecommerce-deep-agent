# 电商智能分析助手（DeepAgents）

基于 **DeepAgents + LangGraph** 的多智能体系统，面向电商业务场景：由主智能体统一规划，按需调度网络搜索、数据库查询、内部知识库三类子智能体获取信息，并自动产出 Markdown / PDF 分析报告。

前端通过 HTTP + WebSocket 实时接收执行过程（调用了哪个助手、执行了哪个工具、最终结果）与生成的文件。

---

## 功能特性

- **自主任务规划**：内置 `write_todos`，把复杂需求拆解为可执行步骤并动态调整。
- **多智能体协作**：主智能体按问题边界调度三个专业子智能体，边界不清时三者并用。
  - **网络搜索助手**：行业动态、竞品信息、市场趋势等公开信息（Tavily）。
  - **数据库查询助手**：商品、订单、用户、库存等业务明细（MySQL）。
  - **RAGFlow 助手**：运营规范、商品资料、售后政策等企业内部知识。
- **文档自动生成**：Markdown 一键生成，并可转换为 PDF。
- **文件上传解析**：支持读取上传的 Markdown / Word / PDF / Excel 并纳入分析。
- **实时过程推送**：WebSocket 按会话隔离推送 `session_created` / `assistant_call` / `tool_start` / `task_result` / `error` 事件。
- **会话级文件隔离**：每个会话独立工作目录，产出文件互不干扰，并可通过接口安全下载。

## 系统架构

```
                ┌─────────────────────────────┐
   HTTP/WS ───► │  FastAPI (api/server.py)     │
                └──────────────┬──────────────┘
                               │
                ┌──────────────▼──────────────┐
                │  主智能体 (agent/main_agent) │  ← 规划 / 汇总 / 生成文档
                └───┬──────────┬──────────┬───┘
                    │          │          │
        ┌───────────▼──┐ ┌─────▼──────┐ ┌─▼────────────┐
        │ 网络搜索助手 │ │ 数据库助手 │ │ RAGFlow 助手 │
        │  Tavily      │ │  MySQL     │ │  知识库      │
        └──────────────┘ └────────────┘ └──────────────┘
```

## 目录结构

```
.
├── agent/                 # 智能体定义
│   ├── llm.py             # 模型初始化（DeepSeek，OpenAI 兼容接口）
│   ├── prompts.py         # 加载 prompt/prompts.yml
│   ├── main_agent.py      # 主智能体构建与流式执行
│   └── subagents/         # 三个子智能体
├── api/                   # 服务层
│   ├── server.py          # FastAPI 接口（任务 / 上传 / 文件 / 下载 / WebSocket）
│   ├── monitor.py         # 埋点单例，负责向对应会话推送事件
│   └── context.py         # ContextVar，隔离并发请求的会话上下文
├── prompt/prompts.yml     # 主/子智能体提示词与描述
├── tools/                 # 工具集（搜索 / 数据库 / 知识库 / 文档生成 / 文件读取）
├── utils/                 # 路径解析、Word→PDF 转换、RAGFlow 配置加载
├── requirements.txt
├── .env.example
└── output/                # 运行期生成（已 gitignore）
```

## 环境要求

- Python 3.10+（开发环境为 3.12）
- MySQL 8.x（可选，用于业务数据查询）
- RAGFlow 服务（可选，用于内部知识检索）
- 转换 PDF 需要本机安装 Microsoft Word（Windows）

## 快速开始

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

# 2. 配置环境变量
copy .env.example .env            # Windows（macOS/Linux 用 cp）
# 然后编辑 .env，填入自己的 Key

# 3. 启动服务
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

服务启动后：

- 接口文档：<http://localhost:8000/docs>
- WebSocket：`ws://localhost:8000/ws/{thread_id}`

## 环境变量

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API Key（也可放在 `.env` 中） |
| `DEEPSEEK_MODEL` | 否 | 模型名，默认 `deepseek-chat` |
| `DEEPSEEK_BASE_URL` | 否 | 接口地址，默认 `https://api.deepseek.com` |
| `TAVILY_API_KEY` | 是 | 联网搜索 Key |
| `RAGFLOW_API_URL` / `RAGFLOW_API_KEY` | 否 | 内部知识库地址与密钥 |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | 否 | 业务数据库连接 |

## 接口说明

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/task` | 提交任务，body: `{ "query": "...", "thread_id": "..." }`，立即返回 `thread_id` |
| `POST` | `/api/upload` | 上传文件（multipart），字段 `files` 与 `thread_id` |
| `GET` | `/api/files?path=...` | 列出会话工作目录中的产出文件 |
| `GET` | `/api/download?path=...` | 下载产出文件（仅允许 `output/` 目录内） |
| `WS` | `/ws/{thread_id}` | 接收该会话的实时事件推送 |

WebSocket 事件体格式：

```json
{
  "type": "monitor_event",
  "event": "tool_start | assistant_call | task_result | session_created | error",
  "message": "人类可读的描述",
  "data": { },
  "timestamp": "2026-01-01T00:00:00"
}
```

## 技术栈

DeepAgents · LangGraph · LangChain · FastAPI · WebSocket · MySQL · Tavily · RAGFlow · python-docx / pypdf / pandas / pywin32
