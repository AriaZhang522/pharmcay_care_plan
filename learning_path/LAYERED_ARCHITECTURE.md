# 分层架构（Layered Architecture）— Django 里的三层

**分层架构的英文**：**Layered Architecture**（有时也叫 **N-tier** 或 **multi-layer architecture**）。

---

## 你说的三类事情 → 三层

| 做的事 | 英文常用叫法 | Django 里通常放在哪个文件 | 命名约定 | 为什么这样分 |
|--------|----------------|----------------------------|----------|--------------|
| 1. 接收 HTTP 请求、返回 HTTP 响应 | **Presentation / Transport / API layer** | **`views.py`** | 复数也可：`views/` 目录，每个文件一个或一组接口 | Django 约定：URL → view；view 只负责「读请求、调下层、写响应」，保持薄薄一层，方便换协议（如以后加 GraphQL）或测试。 |
| 2. 数据格式转换（前端 JSON ↔ 后端 Python/ORM） | **Serialization / DTO / Schema layer** | **`serializers.py`**（或 `schemas.py`） | 不用 DRF 时也可用 `serializers.py` 或 `api/schemas.py` | 把「API 长什么样」集中在一处：校验、转成 Model/字典、转成 JSON。前端契约清晰，改格式只改这里。 |
| 3. 业务逻辑（调 LLM、入队、操作 DB） | **Business logic / Service / Application layer** | **`services.py`**（或 `services/` 包） + **`tasks.py`**（异步任务） | `services.py` 或 `app/services/` 目录 | 不依赖 HTTP，可被 view、Celery task、CLI 共用；单元测试只测这一层即可。`tasks.py` 放「异步入口」，内部尽量调 `services`，避免重复逻辑。 |

---

## 文件命名约定与原因（简表）

| 文件 | 职责 | 为什么这样命名 / 分 |
|------|------|----------------------|
| **views.py** | HTTP 进出的唯一入口：解析 request，调 service/serializer，返回 JsonResponse | Django 惯例；名字就表示「这一层是视图/接口」。 |
| **urls.py** | 路由：URL → view 函数 | Django 惯例；和 views 一起构成「表现层」。 |
| **serializers.py** | 请求体/响应体 ↔ 内部数据结构（dict、Model） | 和 DRF 的 Serializer 概念一致；没有 DRF 时自己写函数/类，名字表示「序列化/反序列化」。 |
| **services.py** | 业务编排：创建 Order/CarePlan、入队、查库等 | 业界常用名；表示「给上层提供的服务」，和「HTTP」解耦。 |
| **models.py** | 数据模型与表结构 | Django 惯例；ORM 定义。 |
| **tasks.py** | Celery 任务：异步执行的入口，内部调 services/llm | 表示「异步任务」，和同步的 views 区分开。 |
| **llm.py** | 调用 LLM（或 mock） | 外部依赖封装，可视为「适配器」；算在「业务/基础设施」边界。 |

---

## 数据流（简化）

```
HTTP Request
    → urls.py  →  views.py（只做：解析请求、调下层、拼响应）
                        → serializers.py（body → 内部 dict；Model → 响应 dict）
                        → services.py（业务：创建订单、入队、查库）
                              → models.py（ORM）
                              → tasks.py（.delay）
    → JsonResponse  ←  views.py
```

---

## 面试一句（中英）

- **EN:** “We use a layered architecture: views for HTTP, serializers for request/response shape, and services for business logic so we can test and reuse logic without HTTP.”
- **中文：** 「我们做分层：views 管 HTTP，serializers 管前后端数据格式，services 管业务逻辑，这样业务不绑在 HTTP 上，好测、好复用。」

---

## 当前项目里的对应关系（careplan-mvp/backend/app）

| 文件 | 职责 |
|------|------|
| **views.py** | 只做：解析 request.body、调 service/serializer、返回 JsonResponse。 |
| **serializers.py** | `order_to_response_dict`、`order_to_list_item`、`care_plan_to_status_payload`：Model → 前端 dict。 |
| **services.py** | `create_order_and_enqueue_care_plan(body)`：创建 Order/CarePlan、入队 Celery。 |
| **tasks.py** | Celery 任务入口，内部调 llm + Model 写库。 |
| **urls.py** | 路由。**models.py** = ORM。**llm.py** = 调用 Claude 或 mock。 |
