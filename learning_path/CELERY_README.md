# Celery 异步任务说明

## 功能

- **任务** `generate_care_plan_task(care_plan_id)`：根据 care_plan_id 查订单 → 调 LLM 生成 Care Plan → 写回 DB（completed/failed）。
- **失败重试**：最多重试 3 次，指数退避（第 1/2/3 次重试前等待 1s、2s、4s）。
- **前端**：不轮询、不 SSE、不自动更新；需手动刷新并点订单才能看到已完成的 Care Plan。

## BRPOP 方式会消失吗？

会。已改为 Celery：

- **之前**：API 把 `care_plan_id` 用 `LPUSH` 放进 Redis 列表，手写 worker 用 `BRPOP` 取任务并处理。
- **现在**：API 调用 `generate_care_plan_task.delay(care_plan_id)`，Celery 把任务发到 Redis（作为 broker），**Celery worker** 从 Redis 取任务并执行。  
Redis 仍在使用，但由 Celery 管理队列，不再手写 BRPOP。原来的 `run_care_plan_worker` 管理命令保留在代码里，但 Docker 里已改为跑 `celery_worker`。

## 如何验证 Celery 在工作

### 1. 看 Celery 进程和日志

```bash
cd careplan-mvp
docker compose up --build
```

终端里应看到 **celery_worker** 的日志，例如：

- `celery@xxx ready.`
- 提交一单后会出现：`Received task: app.tasks.generate_care_plan_task[xxx]`
- 成功后：`Task app.tasks.generate_care_plan_task[xxx] succeeded in Xs`

说明 worker 在跑且接到了任务。

### 2. 从前端验证

1. 打开 http://localhost:5173，填表单提交 → 立刻看到「已收到」和 order_id。
2. 等约 10～20 秒。
3. 点左侧 **Refresh**，再点刚提交的订单。
4. 右侧应出现完整 Care Plan（Problem List、Goals 等）。  
若不刷新、不点订单，不会自动更新，符合「不自动更新前端」的设计。

### 3. 看数据库

在 DBeaver 或 psql 里查该订单对应的 `care_plans`：

```sql
SELECT id, order_id, status, problem_list, updated_at
FROM care_plans
ORDER BY updated_at DESC
LIMIT 5;
```

若 `status = 'completed'` 且 `problem_list` 有内容，说明 Celery 任务已执行并写库。

### 4. 用假 LLM 测试（不花钱、不等待）

设置环境变量 `USE_FAKE_LLM=1` 后，`call_llm_for_care_plan` 不会调 Claude API，而是直接返回一段固定的 care plan 文本（结构相同）。Worker 流程照常跑通，适合本地/CI 验证。

**Docker：** 在 `docker-compose.yml` 里给 `celery_worker` 和（若需要）`backend` 加环境变量：

```yaml
environment:
  USE_FAKE_LLM: "1"
```

**本机：**

```bash
export USE_FAKE_LLM=1
celery -A app.celery worker -l info
```

### 5. 本机单独跑 worker（可选）

不跑 Docker 时，先起 Redis、Postgres，再在 backend 目录：

```bash
cd careplan-mvp/backend
export CELERY_BROKER_URL=redis://localhost:6379/0
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
# ... 其他 DB、ANTHROPIC_API_KEY
celery -A app.celery worker -l info
```

提交一单后，此终端应打印 Received task / succeeded。

## 重试行为

任务内若抛异常，Celery 会按 `max_retries=3` 和 `countdown=2**retries`（1、2、4 秒）重试； 3 次重试仍失败则标记该 CarePlan 为 `failed` 并写入 `error_message`，不再重试。
