# Care Plan MVP — 代码结构 & 断点调试指南

## 一、请求从哪进、调了谁（以「生成 Care Plan」为例）

```
浏览器/前端  POST http://localhost:8000/api/generate-care-plan/
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  Django 根据 ROOT_URLCONF = "app.urls" 找路由                      │
│  文件: app/urls.py                                                │
└──────────────────────────────────────────────────────────────────┘
       │
       │  path("api/generate-care-plan/", views.generate_care_plan)
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  views.generate_care_plan(request)                                │
│  文件: app/views.py  第 92 行附近                                  │
│  • 解析 JSON body → 校验 mrn / npi                                 │
│  • Patient.objects.get_or_create(...)   →  app/models.py Patient   │
│  • ReferringProvider.objects.get_or_create(...) → models ReferringProvider │
│  • Order.objects.create(...)           →  models Order            │
│  • CarePlan.objects.create(...)        →  models CarePlan         │
│  • care_plan_obj.status = PROCESSING; save()                       │
│  • call_llm_for_care_plan(order_dict) → 同文件 第 17 行           │
│  • 把 LLM 返回写回 care_plan_obj，status=COMPLETED，save()         │
│  • return JsonResponse({ order_id, care_plan })                    │
└──────────────────────────────────────────────────────────────────┘
       │
       │  call_llm_for_care_plan(order_dict)
       ▼
┌──────────────────────────────────────────────────────────────────┐
│  app/views.py  call_llm_for_care_plan()  第 17 行                  │
│  • 用 settings.ANTHROPIC_API_KEY 调 Claude API                    │
│  • 解析 JSON 返回 → 返回 dict                                     │
└──────────────────────────────────────────────────────────────────┘
```

**三个接口对应关系：**

| 接口 | 文件 | 函数 |
|------|------|------|
| POST /api/generate-care-plan/ | app/views.py | generate_care_plan |
| GET /api/orders/ | app/views.py | list_orders |
| GET /api/orders/<order_id>/ | app/views.py | get_order |

**为什么这样设计？**

- **一个 app 包**：Django 习惯按「应用」分，这里只有一个业务就一个 `app`（models + views + urls）。
- **路由在 app/urls.py**：`ROOT_URLCONF = "app.urls"`，所以所有 URL 直接在 `app/urls.py` 里写，每个 path 指向 `views.xxx`。
- **views 里写业务**：解析请求、调 models 读写 DB、调 LLM、拼 JsonResponse。没有单独「service 层」是为了简单；以后要拆可以再抽成 `app/services.py` 等。

**其他常见写法（简要）：**

- 用 **class-based views (CBV)**：一个 URL 一个类，可复用 mixin，适合复杂权限/多方法。
- 拆 **service 层**：views 只做 HTTP，业务逻辑放到 `services/care_plan.py`，便于单测和复用。
- 用 **Django REST framework (DRF)**：序列化、权限、限流更现成，但当前项目没用，保持简单。

---

## 二、断点怎么加、从前往后跟一条请求

建议**按调用顺序**在下面这些地方打断点，跑一次「生成 Care Plan」就能从前跟到后。

### 1. 入口：接口进到哪个函数

**文件：** `app/urls.py`  
**位置：** 第 5 行（或任意一行，只是方便确认「路由被用到」）

- 在行号左侧点击，出现红点 = 断点。
- 注意：Django 路由是配置，真正「进函数」的断点在下一条。

### 2. 真正入口：view 函数第一行

**文件：** `app/views.py`  
**函数：** `generate_care_plan(request)`  
**建议断点：** 第 92 行（函数体第一行，如 `def generate_care_plan(request):` 下面那行）

- 这里停住 = 请求已经路由到该接口。
- 看 **Variables** 里 `request.body`、后续的 `body`（解析后的 dict）。

### 3. 数据库：创建/查询病人和医生

**文件：** `app/views.py`  
**建议断点：**
- 第 111 行：`Patient.objects.get_or_create(...)` 前一行
- 第 119 行：`ReferringProvider.objects.get_or_create(...)` 前一行
- 第 124 行：`Order.objects.create(...)` 前一行
- 第 134 行：`CarePlan.objects.create(...)` 前一行

- 单步 **Step Over (F10)** 后看 `patient`、`provider`、`order`、`care_plan_obj` 的值。
- 实际 DB 访问在 **app/models.py** 的 `Patient` / `ReferringProvider` / `Order` / `CarePlan`，Django ORM 会转成 SQL；若想跟进去，可在模型类里打断点（一般不必要）。

### 4. 调 LLM 前后

**文件：** `app/views.py`  
**建议断点：**
- 第 154 行：`result = call_llm_for_care_plan(order_dict)` 这一行
- 第 17 行：`def call_llm_for_care_plan(order_dict):` 下面第一行（进 LLM 函数）

- 在 154 停住时看 `order_dict`。
- **Step Into (F11)** 进 `call_llm_for_care_plan`，再在 44 行（`client.messages.create`）前后看请求/响应（可选）。
- 从 `call_llm_for_care_plan` 返回后，在第 155–161 行看 `result` 和写回 `care_plan_obj` 的字段。

### 5. 返回响应

**文件：** `app/views.py`  
**建议断点：** 第 179 行 `return JsonResponse(...)` 这一行

- 看返回的 `order_id` 和 `care_plan` 内容。

---

## 三、在 Cursor / VS Code 里怎么操作

### 1. 用已有「Django 本地跑后端」配置

- 左侧点 **Run and Debug (Ctrl+Shift+D / Cmd+Shift+D)**。
- 顶部下拉选：**「Django: 本地跑后端 (可断点 views.py)」**。
- 在 `app/views.py`、`app/urls.py` 按上面位置点行号左侧加断点。

### 2. 启动调试

- 按 **F5** 或点绿色 **Run**。
- 后端会以 `manage.py runserver 0.0.0.0:8000` 跑起来，并停在断点上。

### 3. 触发请求

- 浏览器打开前端 http://localhost:5173，填表单点「Generate Care Plan」；  
  或用 curl：
  ```bash
  curl -X POST http://localhost:8000/api/generate-care-plan/ \
    -H "Content-Type: application/json" \
    -d '{"patient_mrn":"M1","referring_provider_npi":"N1","patient_first_name":"A","patient_last_name":"B","medication_name":"X","primary_diagnosis":"I10","patient_records":"notes"}'
  ```

### 4. 调试时常用键

| 键 | 作用 |
|----|------|
| **F5** | 继续运行到下一个断点 |
| **F10** | Step Over（当前行执行完，不进入函数） |
| **F11** | Step Into（进入当前行的函数） |
| **Shift+F11** | Step Out（跳出当前函数） |

- **Variables**：看当前作用域变量。
- **Call Stack**：看当前是从哪一层调进来的（例如：`generate_care_plan` → Django 内部）。

### 5. 本地调试时连数据库

- 若 Postgres 在 Docker 里、端口是 **5433**，在 `careplan-mvp/.env` 里加（或确认）：
  ```bash
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5433
  POSTGRES_USER=careplan
  POSTGRES_PASSWORD=131421Zyy!
  POSTGRES_DB=careplan
  ```
- launch 配置里已用 `"envFile": "${workspaceFolder}/careplan-mvp/.env"`，所以 F5 会读这些变量，连到本机 5433 的库。

---

## 四、GET 接口的断点（可选）

- **GET /api/orders/**  
  **文件：** `app/views.py`  
  **函数：** `list_orders(request)`  
  在 **第 196 行**（函数第一行）打断点即可。

- **GET /api/orders/<order_id>/**  
  **文件：** `app/views.py`  
  **函数：** `get_order(request, order_id)`  
  在 **第 218 行**（函数第一行）打断点即可。

这样你就能从「请求进哪个接口」→「调了哪个文件的哪个 function」→「下一步是哪个」完整跟一遍。
