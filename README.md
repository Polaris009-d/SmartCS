# SmartCS - 企业级智能电商客服平台

> Enterprise Intelligent E-commerce Customer Service & Automation Platform

基于 **RAG + Agent + Workflow** 架构，参考 Chatwoot 业务模型，覆盖售前咨询 → 订单服务 → 售后处理的完整客服闭环。

---

## 架构概览

```
用户消息 → Channel Adapter → MessageBuilder → EventDispatcher
                                    │
                          ┌─────────┼─────────┐
                          ▼         ▼         ▼
                      OrderAgent  Logistics  RefundAgent
                          │         │         │
                          └─────────┼─────────┘
                                    ▼
                              SafetyEngine (Pydantic)
                                    │
                          ┌─────────┼─────────┐
                          ▼                   ▼
                      RAG Pipeline       Agent Audit Log
                   (Embedding+BM25+LLM)
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + SQLAlchemy 2.0 async |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存 | Redis 7 |
| LLM | deepseek-chat (可配置 OpenAI/Anthropic/Local) |
| RAG | pgvector 向量检索 + PostgreSQL 全文检索 + RRF 融合 + jieba 分词 |
| Agent | LangChain Tool + 自研 Pydantic 安全引擎 |
| 实时通信 | SSE (Server-Sent Events) |
| 前端 | Vue 3 + Element Plus + Pinia + ECharts |

## 快速启动

### 前置依赖

- Python 3.12+
- PostgreSQL 16 + pgvector 扩展
- Redis 7+
- Node.js 20+

### 启动

```bash
# 1. PostgreSQL
D:\APP\PostgreSQL\bin\pg_ctl.exe -D D:\APP\PostgreSQL\data start

# 2. Redis
D:\APP\redis\memurai.exe

# 3. Embedding 服务（加载本地模型，需用 conda Python）
D:\APP\anaconda3\python.exe D:\落地项目\SmartCS\backend\scripts\embed_server.py --port 8001

# 4. 后端 API
cd D:\落地项目\SmartCS\backend && .venv\Scripts\python -m uvicorn app.main:app --port 8000

# 5. 前端
cd D:\落地项目\SmartCS\frontend && npx vite --port 5173
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| API | http://localhost:8000/docs |

测试账号：admin@smartcs.com / admin123

## API 端点

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 登录，返回 JWT |
| POST | /api/v1/auth/register | 注册 |
| GET | /api/v1/auth/me | 当前用户信息 |

### 渠道

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/inboxes | 渠道列表 |
| POST | /api/v1/inboxes | 创建渠道 |
| GET | /api/v1/inboxes/{id} | 渠道详情 |
| PATCH | /api/v1/inboxes/{id} | 更新渠道 |
| DELETE | /api/v1/inboxes/{id} | 删除渠道 |

### 联系人

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/contacts | 联系人列表 |
| GET | /api/v1/contacts/search?q= | 搜索联系人 |
| GET | /api/v1/contacts/{id} | 联系人详情 |

### 会话

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/conversations | 会话列表（筛选：inbox/status/agent） |
| POST | /api/v1/conversations | 创建会话 |
| GET | /api/v1/conversations/{id} | 会话详情 + 消息 |
| PATCH | /api/v1/conversations/{id} | 更新状态/分配 |
| POST | /api/v1/conversations/{id}/assign | 手动分配 |
| POST | /api/v1/conversations/{id}/resolve | 标记解决 |
| POST | /api/v1/conversations/{id}/snooze | 暂缓 |

### 消息

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/conversations/{id}/messages | 发送消息 → SSE 流式返回 AI 回复 |
| GET | /api/v1/conversations/{id}/messages | 消息历史 |
| GET | /api/v1/conversations/{id}/stream | SSE 订阅端点 |

### 知识库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/knowledge/documents | 上传文档入库 |
| GET | /api/v1/knowledge/documents | 文档列表 |
| DELETE | /api/v1/knowledge/documents/{id} | 删除文档 |
| GET | /api/v1/knowledge/search?q=&top_k= | 混合检索 |

### Agent

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/agent/order/query | 按订单号查询 |
| GET | /api/v1/agent/order/query-by-contact?contact_id= | 按联系人查所有订单 |
| POST | /api/v1/agent/logistics/query | 物流查询 |
| POST | /api/v1/agent/refund | 退款申请（安全校验） |
| GET | /api/v1/agent/logs | 审计日志查询 |

### 工单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tickets | 工单列表（筛选：status/type） |
| POST | /api/v1/tickets | 创建工单 |
| GET | /api/v1/tickets/{id} | 工单详情 |
| PATCH | /api/v1/tickets/{id} | 更新工单 |
| POST | /api/v1/tickets/{id}/assign | 分配工单 |

### 情感预警

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/sentiment/alerts | 预警列表（筛选：level/escalated） |

### 绩效看板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/dashboard/performance?days=7 | 核心指标统计 |

## SSE 事件协议

| 事件 | 说明 |
|------|------|
| `thinking` | AI 开始思考 |
| `ai_chunk` | AI 流式逐字输出 |
| `ai_done` | AI 回复完成，含置信度和来源 |
| `agent_action` | Agent 操作结果（订单/物流/退款） |
| `sentiment_alert` | 情感预警触发 |
| `handoff` | AI 置信度低，转人工 |
| `conversation.updated` | 会话状态/分配变更 |
| `keepalive` | 30s 心跳 |

## 项目结构

```
SmartCS/
├── GUIDE.md              # 详细实施方案
├── README.md             # 本文件
├── backend/
│   ├── app/
│   │   ├── core/         # 配置、数据库、Redis、JWT、EventBus
│   │   ├── models/       # 13 个 ORM 模型
│   │   ├── schemas/      # Pydantic 请求/响应
│   │   ├── api/v1/       # REST API 路由
│   │   ├── services/     # 业务逻辑层
│   │   ├── channels/     # 渠道适配器（策略模式）
│   │   ├── rag/          # RAG 子系统
│   │   ├── agents/       # Agent + 安全引擎 + Tools
│   │   ├── llm/          # LLM 提供商抽象
│   │   └── tasks/        # 后台定时任务
│   ├── alembic/          # 数据库迁移
│   ├── scripts/          # 种子数据
│   └── tests/            # 测试用例
└── frontend/
    └── src/
        ├── views/        # Login/Workspace/ConversationList/ChatWindow/Knowledge/Dashboard/Tickets
        ├── components/   # MessageBubble/StreamingText/AgentActionCard
        ├── stores/       # Pinia (auth/conversation/message)
        └── utils/        # SSE客户端
```

## 核心功能演示

打开 http://localhost:5173 登录后：

| 输入 | AI 行为 |
|------|---------|
| `你好` | RAG 检索 + LLM 生成欢迎语 |
| `175cm 70kg 买什么尺码` | 知识库检索尺码表 → LLM 推荐 |
| `退货政策是什么` | RAG 检索售后政策 → LLM 回答 |
| `查订单` / 下拉选订单 | Agent 查库返回订单详情 |
| `查物流` / 下拉选已发货订单 | Agent 返回物流轨迹 |
| `退款` / 下拉选订单 | Agent 安全校验 → 自动退款或风控拦截 |
| 不满消息 | 情感预警触发 → SSE 弹窗告警 → 自动升级工单 |
