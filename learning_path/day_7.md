# Debug Virtual Env
```
cd /Users/zhangyuyan/Desktop/pharmacy_career_plan/careplan-mvp/backend
source .venv/bin/activate
```
# 代码拆分迁移表 — views.py → serializers / services

拆分后 API 行为不变，已在 Docker 中验证通过。

---

## 代码迁移表（从原 views.py 搬到哪个文件）


| 原 views.py 中的代码 / 逻辑                                                      | 搬到了                | 新位置（函数名）                                              |
| ------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------- |
| `json.loads(request.body)` 解析请求体                                          | **serializers.py** | `parse_request_body(body)`                            |
| 构建 `{"message", "order_id", "care_plan_id"}` 响应                           | **serializers.py** | `build_generate_care_plan_response(order, care_plan)` |
| `_order_to_response_dict(order)`：Order + CarePlan → 前端完整订单 dict           | **serializers.py** | `order_to_response_dict(order)`                       |
| list 中每个 order 转成 `{order_id, created_at, patient_name, medication_name}` | **serializers.py** | `order_to_list_item(o)`                               |
| CarePlan → `{status, content?, error_message?}` 响应                        | **serializers.py** | `care_plan_to_status_payload(care_plan)`              |
| mrn/npi 必填校验                                                              | **serializers.py** | `validate_generate_care_plan_body(body)`              |
| dob 解析、Patient/Provider get_or_create、Order/CarePlan 创建、task.delay        | **services.py**    | `create_order_and_enqueue_care_plan(body)`            |
| `Order.objects.select_related("patient").order_by("-created_at")`         | **services.py**    | `get_all_orders_for_list()`                           |
| `CarePlan.objects.filter(id=id).first()`                                  | **services.py**    | `get_care_plan_by_id(id)`                             |
| `Order.objects.filter(uuid=...).select_related(...).first()`              | **services.py**    | `get_order_by_uuid(uuid)`                             |
| 接收请求、捕获异常、调用 service/serializer、返回 JsonResponse                           | **views.py**（保留）   | 各 view 函数                                             |


---

## 拆分后三层职责


| 文件                 | 职责                                |
| ------------------ | --------------------------------- |
| **views.py**       | 只负责接收请求、返回响应；不查库、不写业务逻辑。          |
| **serializers.py** | 数据校验和格式转换（请求体解析、Model → 响应 dict）。 |
| **services.py**    | 业务逻辑（DB 查询、创建订单、入队 Celery）。       |


# POST /api/generate-care-plan/ 请求流程（从前到后）

> 说明：项目里创建订单的接口是 **POST /api/generate-care-plan/**，不是 POST /api/orders/。下面按这个接口说明。

---

## 流程图（简化）

```
HTTP Request (JSON body)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. urls.py                                                       │
│    匹配 "api/generate-care-plan/" → 调用 views.generate_care_plan │
│    数据：无变化，只是路由                                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. views.py · generate_care_plan(request)                         │
│    - 拿到 request.body (bytes)                                    │
│    - 调用 parse_request_body(request.body)                        │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. serializers.py · parse_request_body(body: bytes)               │
│    输入：request.body (bytes)，如 b'{"patient_mrn":"x","ref..."}' │
│    输出：dict，如 {"patient_mrn":"x","referring_provider_npi":"y"...} │
│    转换：JSON 字符串(bytes) → Python dict                         │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼ body (dict) 返回 views
    │
┌─────────────────────────────────────────────────────────────────┐
│ 4. views.py                                                       │
│    - 调用 validate_generate_care_plan_body(body)                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. serializers.py · validate_generate_care_plan_body(body: dict)  │
│    输入：body (dict)                                              │
│    输出：None（无返回值，校验失败则 raise ValueError）           │
│    作用：检查 mrn、npi 必填                                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼ 校验通过，返回 views
    │
┌─────────────────────────────────────────────────────────────────┐
│ 6. views.py                                                       │
│    - 调用 create_order_and_enqueue_care_plan(body)                │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. services.py · create_order_and_enqueue_care_plan(body: dict)   │
│    输入：body (dict)                                              │
│    做：解析 dob、get_or_create Patient/Provider、                 │
│        create Order、create CarePlan、generate_care_plan_task.delay() │
│    输出：(order: Order, care_plan: CarePlan)                       │
│    转换：dict → ORM 实例 + 写入 DB + 投递 Celery 任务             │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼ order, care_plan 返回 views
    │
┌─────────────────────────────────────────────────────────────────┐
│ 8. views.py                                                       │
│    - 调用 build_generate_care_plan_response(order, care_plan)     │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. serializers.py · build_generate_care_plan_response(...)        │
│    输入：order (Order), care_plan (CarePlan)                      │
│    输出：dict，如 {"message":"已收到","order_id":"uuid","care_plan_id":5} │
│    转换：ORM 实例 → 响应 dict                                     │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼ response_dict 返回 views
    │
┌─────────────────────────────────────────────────────────────────┐
│ 10. views.py                                                      │
│     - return JsonResponse(response_dict)                          │
│     输出：HTTP 200 + JSON body                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 数据格式变化一览

| 步骤 | 文件 | 函数 | 输入格式 | 输出格式 |
|------|------|------|----------|----------|
| 1 | urls.py | 路由 | HTTP 请求 | → views.generate_care_plan |
| 2 | views.py | generate_care_plan | request (HttpRequest) | - |
| 3 | serializers.py | parse_request_body | body: `bytes` (JSON 原始字节) | `dict` |
| 4 | views.py | - | body: `dict` | - |
| 5 | serializers.py | validate_generate_care_plan_body | body: `dict` | `None`（或抛错） |
| 6 | views.py | - | body: `dict` | - |
| 7 | services.py | create_order_and_enqueue_care_plan | body: `dict` | `(Order, CarePlan)` |
| 8 | views.py | - | order, care_plan | - |
| 9 | serializers.py | build_generate_care_plan_response | order, care_plan | `dict` |
| 10 | views.py | JsonResponse | response_dict | HTTP 响应 |

---

## 断点顺序与 pdb 用法

当前在以下位置加入了 `breakpoint()`，触发顺序与所在步骤如下：

| 断点 | 文件 | 位置 | 可查看的变量 |
|------|------|------|--------------|
| DEBUG 1 | views.py | generate_care_plan 入口 | `request`, `request.body` |
| DEBUG 2 | views.py | 校验通过后 | `body` (dict) |
| DEBUG 3 | views.py | service 返回后 | `order`, `care_plan` |
| DEBUG 4 | serializers.py | parse_request_body 入口 | `body` (bytes) |
| DEBUG 5 | serializers.py | parse_request_body 返回前 | `result` (dict) |
| DEBUG 6 | serializers.py | validate 入口 | `body` (dict) |
| DEBUG 7 | serializers.py | build_generate_care_plan_response 入口 | `order`, `care_plan` |
| DEBUG 8 | services.py | create_order_and_enqueue_care_plan 入口 | `body` (dict) |
| DEBUG 9 | services.py | create_order_and_enqueue_care_plan 返回前 | `order`, `care_plan` |

**运行方式：**

```bash
cd careplan-mvp/backend
# 本地运行（支持 pdb 交互）
python manage.py runserver
```

然后在另一个终端发送请求：

```bash
curl -X POST http://127.0.0.1:8000/api/generate-care-plan/ \
  -H "Content-Type: application/json" \
  -d '{"patient_mrn":"debug-test","referring_provider_npi":"1234567890"}'
```

**pdb 常用命令：** `c` 继续到下一断点；`n` 单步；`p 变量名` 打印变量；`q` 退出。

> 用 Docker 时需加 `-it` 才能交互：`docker compose run --rm -it backend python manage.py runserver 0.0.0.0:8000`。调试结束后删除所有 `breakpoint()`。



