Redis only saves the data and don't do  any actions on that. 

In the full-stack project, Redis saves the key of the ID, but in the RAG project, it saves the key-value and the history dialogue.

But when I use AWS SQS and the Lambda service, it is a push model, not a pull model. In today's learning, I need to write a worker to pull the tasks.

How often should it be pulled?
What if the LLM call fails?



## The difference between BRPOP and polling is:

1. BRPOP
   When a task enters the message queue (Redis), it is pushed to the workers immediately. BRPOP has a waiting timeout period, during which any incoming task can be processed instantly.

2. Polling
   The worker checks for tasks at a set interval (e.g., every 3 seconds). If the worker checks and there are no tasks available, the worker will sleep for three cycles or three seconds.

## What if the LLM call fails?

I think the answer is that the system automatically tries three more times. We can set the maximum number of attempts to three, and each retry interval can be set to get progressively longer.

If those three attempts fail:
1. We change the status to "Failed."
2. The user can manually click "Regenerate."

## What does exponential backoff mean? 
It means the waiting time for each retry gets longer based on an exponential scale, instead of waiting the same amount of time every time.


```
┌─────────────┐  ①请求   ┌─────────────┐
│    前端     │ ───────→ │ Web Server  │
│  (React)    │          │  (Django)   │
└─────────────┘          └──────┬──────┘
      ▲                         │
      │                         ├────②存数据────→ ┌─────────────┐
      │                         │  (status=       │  Database   │
      │                         │   pending)      │ (PostgreSQL)│
      │                         │  ←──返回成功──   └─────────────┘
      │                         │
      │                         ├────③放任务────→ ┌─────────────┐
      │                         │  (careplan_id)  │    Redis    │
      │                         │  ←──返回成功──   │   (队列)    │
      │     ④返回"收到了"        │                 └──────┬──────┘
      └─────────────────────────┘                       ▲
                                                        │ ⑤取任务
                                                        │
                                                 ┌─────────────┐
                                                 │   Worker    │
                                                 │  (Celery)   │
                                                 └──────┬──────┘
                                                        │
                                                        │ ⑥调用 LLM
                                                        │
                                                        ├────⑦更新数据────→ 
                                                        ｜Database
							                                          ｜ (status=completed)
                                                        │  ←────返回成功────
                                                        │
                                                        ⑧ 然后呢？
                                                        前端不知道！
 ```


 ## Microservice character
Each service is independent, allowing for:
1. Independent expansion
2. Independent deployment
3. Fault isolation

If you want to expand the web service, you can just expand that specific service instead of changing the whole structure.

However, there are several problems:
1. Since each service is independent, if workers finish their task on a web service, they don't know the result automatically.
2. It is difficult for a programmer to debug because a problem can exist in any service.
3. It introduces internet-related issues because services communicate with each other via the internet at each stage.

## Why split a project into a web service and a worker?

The reason is that calling an LLM takes time. If the user has to wait for the process to finish, the wait time is too long. By using this architecture, when a user fills out a patient information form, the task is sent to the backend and the user can immediately submit another form. This is much more user-friendly and improves the overall user experience.

Additionally, using workers allows the system to expand independently. When workers are busy, I can simply spin up several more workers to handle the heavy task load.

Synchronous/ˈsɪŋkrənəs/ and asynchronous/eɪˈsɪŋkrənəs/




## 我今天学了手写 Worker、Celery、微服务的概念。现在我把我的理解讲给你，你帮我判断有没有差错，或者可以补充的地方。

1. 手写 Worker vs 用 Celery，各自的优缺点是什么？
2. LLM 调用失败的时候，Celery 会怎么处理？（重试策略是什么？）
3. 一个程序搞定所有事 vs 拆成多个微服务，各自的优缺点是什么？
4. 面试官问"LLM 调用失败怎么办"，我打算这样回答：[你的回答]

我的回答是：今天我手动编写了 Worker 代码，并使用了相关的重试点。在手动编写 Worker 时，虽然我不确定具体的优势，但明显的缺点是需要编写的代码量太多。

我使用的是 BRPOP 方法，这会让 Worker 始终处于等待状态并占用端口。相比之下，使用 Celery 的优势在于它非常易于使用，而且我可以通过 Docker 和 LLM 监控任务摘要，了解 Celery 是否成功发送、接收并处理了任务。

如果不使用 Celery 而增加其他服务，会使整个架构变得更复杂。当 LLM 调用 Celery 时，我们会采用指数退避（Exponential Backoff）机制，尝试重试 3 次，且每次重试的等待时间按指数级增长。

关于使用单一程序处理所有任务还是采用微服务的对比：
1. 单一程序的优点：
   所有服务同步且自动运行。当我提出请求时，可以快速从后端获取答案并传回前端。
2. 微服务的挑战：
   稳定性可能较低，因为服务间的通信依赖于网络。如果后端有了答案，我们需要重新建立与前端的通信，以便前端获知结果。
3. 微服务的优点：
   (a) 每个服务都是独立执行的，便于独立扩展、调试和部署。
   (b) 扩展性强：如果我想扩展 Worker 服务，只需增加该服务而无需更改整个架构。
   (c) 故障隔离：如果一个服务发生错误，不会直接影响到其他服务。
4. 微服务的缺点：
   程序员需要在不同的服务中进行调试，因为很难立刻判断错误具体发生在哪个服务中。

如果面试官问到“LLM 调用失败怎么办”，我的回答是：
我将使用指数退避方法并设置重试次数。最大重试次数为 3 次。如果 3 次尝试后仍然失败，我将把任务状态设置为 Failure，并让用户点击“重新生成”按钮来再次执行任务。




# 手写 Worker / Celery / 微服务 — 理解自检  
# Hand-written Worker / Celery / Microservices — Self-check Q&A

---

## 1. 手写 Worker vs 用 Celery，各自的优缺点？  
## 1. Hand-written Worker vs Celery — Pros and cons?

**你的要点 / Your points**：手写缺点代码量大；BRPOP 让 worker 一直等待、占端口；Celery 易用、可用 Docker 和监控看任务。✅ 方向对。  
*You had: hand-written = more code; BRPOP keeps worker waiting / “uses a port”; Celery = easy to use, Docker + monitoring. ✅ Direction is correct.*

**可补充 / 修正 — Additions & corrections:**

- **「占端口」/ “Uses a port”**  
  **EN:** With BRPOP, the worker is a **Redis client** holding **one Redis connection** in a blocking wait — it does **not** “open a port” to the outside. More accurate: the worker process **holds one Redis connection** while blocking.  
  **中文：** BRPOP 时 worker 是作为 **Redis 的客户端** 连上去等消息，占的是 **Redis 的一条连接**，不是「对外开一个端口」。更准确的说法是：worker 进程会 **一直占着一条 Redis 连接** 在阻塞等待。

- **手写 Worker 的优点 / Hand-written Worker — Pros**  
  **EN:** No Celery dependency, simpler deployment. Full control over logic; the queue just holds `care_plan_id`, easy to reason about. Good for small or simple task shapes.  
  **中文：** 没有 Celery 依赖，部署简单；逻辑完全自己控，队列里就存 care_plan_id，一目了然；适合小项目、任务形态简单时。

- **手写 Worker 的缺点 / Hand-written Worker — Cons**  
  **EN:** You have to implement retry, backoff, and failure handling yourself. Multiple workers / concurrent consumption (e.g. several processes BRPOP the same list) need your own coordination. No built-in task monitoring or retry stats.  
  **中文：** 重试、退避、失败处理都要自己写；多 worker、并发消费要自己处理（例如多个进程都 BRPOP 同一条 list）；没有现成的任务监控、重试统计。

- **Celery 的优点 / Celery — Pros**  
  **EN:** Retry, exponential backoff, and serialization are built in. Multiple workers work out of the box; scale by adding workers. Tools like Flower give task monitoring and visibility.  
  **中文：** 重试、指数退避、序列化都内置；多 worker 开箱即用，加机器即可扩展；有 Flower 等监控、任务状态可查。

- **Celery 的缺点 / Celery — Cons**  
  **EN:** Extra framework and concepts to learn. Extra dependency (broker; we use Redis).  
  **中文：** 多一个框架和概念要学；多一个依赖（broker，你们用 Redis）。

**面试一句 / One-liner for interviews:**  
**EN:** “A hand-written worker fits when logic is simple and we don’t want to add Celery; Celery fits when we need retries, monitoring, and scaling workers — in our project we use Celery for async LLM calls and retries.”  
**中文：** 「手写 worker 适合逻辑简单、不想引入 Celery 时；Celery 适合要重试、监控、多 worker 扩展的场景，我们项目里用 Celery 做了 LLM 调用的异步和重试。」

---

## 2. LLM 调用失败时，Celery 会怎么处理？重试策略是什么？  
## 2. When an LLM call fails, how does Celery handle it? What’s the retry strategy?

**你的要点 / Your points**：指数退避、重试 3 次、等待时间指数增长。✅ 对。  
*You had: exponential backoff, retry 3 times, wait time grows exponentially. ✅ Correct.*

**可补充（和当前代码一致的说法）— In line with our code:**

- **EN:** In the task we **catch the exception**, then: set the CarePlan **status to failed**, save the **error_message**, **persist to DB**, then **raise self.retry(...)**.  
  **中文：** 任务里 **catch 异常** 后：先把该 CarePlan 的 **status 设为 failed**，**error_message 存异常信息**，**写库**，再 **raise self.retry(...)**。

- **EN:** **Retries:** `max_retries=3` means **at most 3 more retries** (so up to 4 runs total). **countdown = 2^retries** → wait **1s, 2s, 4s** before the 1st, 2nd, 3rd retry (exponential backoff).  
  **中文：** **重试**：`max_retries=3`，即**最多再重试 3 次**（加上第一次，一共最多 4 次执行）。**countdown = 2^retries**：第 1/2/3 次重试前分别等 **1s、2s、4s**（指数退避）。

- **EN:** If it still fails after 3 retries: Celery stops; the CarePlan stays **status='failed'**, **error_message** holds the last error; the user can click “Regenerate” to enqueue the task again.  
  **中文：** 若 3 次重试后仍失败：Celery 不再重试，该 CarePlan 保持 **status='failed'**，**error_message** 里是最后一次错误，用户可点「重新生成」再发一次任务。

**面试一句 / One-liner for interviews:**  
**EN:** “On LLM failure we first mark the order as failed in the DB and save the error message, then use Celery retry with at most 3 retries and exponential backoff (e.g. 1s, 2s, 4s). If it still fails we leave it failed and let the user manually trigger regeneration.”  
**中文：** 「LLM 失败时我们先在 DB 里把订单标成 failed 并记错误信息，再用 Celery 的 retry 做最多 3 次重试，每次间隔按指数退避 1s、2s、4s；都失败就保持 failed，由用户手动重新生成。」

---

## 3. 一个程序搞定所有事 vs 拆成多个微服务，各自的优缺点？  
## 3. One app does everything vs. splitting into microservices — Pros and cons?

**你的要点 / Your points**：单体同步拿答案、微服务要重新建连通知前端、微服务可独立扩展和故障隔离、但跨服务调试难。✅ 都对。  
*You had: monolith = sync response; microservices = need another channel to notify frontend; microservices = independent scaling & fault isolation; harder to debug across services. ✅ All good.*

**可微调表述 — Refinements:**

- **单体优点 / Monolith — Pros**  
  **EN:** In one request we can **wait synchronously for the LLM** and then respond to the client; simple to implement and predictable latency. All logic in one process, so the call path is clear when debugging.  
  **中文：** 一次请求里可以 **同步等 LLM 返回** 再给前端，实现简单、延迟可预测；所有逻辑在一个进程，排查时调用链清晰。

- **微服务「后端有答案要通知前端」/ Microservices — Notifying the frontend**  
  **EN:** Because the API already returned “request received”, the worker’s result **cannot be sent back over that HTTP response**. The frontend has to learn “done” via **polling, WebSocket, or another channel**.  
  **中文：** 因为 API 已经先返回了「已收到」，所以 worker 算完后 **不能通过那次 HTTP 响应** 把结果推回去，只能靠 **前端轮询、WebSocket 或别的通道** 让前端知道「完成了」。

- **微服务缺点 / Microservices — Cons**  
  **EN:** Besides “debugging across services”, add: **ops and deployment are more complex** (multiple service types, instances, network and permissions).  
  **中文：** 除了「要在不同服务里排查」，还可以加一句：**运维和部署更复杂**（多类服务、多实例、网络与权限）。

**面试一句 / One-liner for interviews:**  
**EN:** “Monolith is simpler and easier to debug; microservices give independent scaling and fault isolation but add cross-service calls and harder troubleshooting. Our current setup is API + Celery worker — a light form of async split.”  
**中文：** 「单体简单、易调试；微服务便于独立扩展和故障隔离，但跨服务调用和排错更复杂，我们当前是 API + Celery worker 两个进程，算轻量的异步拆分。」

---

## 4. 面试官问「LLM 调用失败怎么办」— 你的回答  
## 4. Interview: “What do you do when an LLM call fails?” — Your answer

**你的回答 / Your answer**：指数退避、最大重试 3 次、仍失败则状态标 Failure、用户点「重新生成」。✅ 足够用。  
*You had: exponential backoff, max 3 retries, then mark status Failure, user clicks “Regenerate”. ✅ Good enough.*

**可加一两句（更完整）— Optional extras for a fuller answer:**

- **EN:** “In the task we **catch exceptions**, set the order **status to failed** and **write the error to error_message** in the DB — that helps debugging and we can show the reason on the frontend later.”  
  **中文：** 「任务里会 **catch 异常**，先把这条订单的 **status 标成 failed**，并把 **错误信息写入 error_message** 存库，方便排查和以后在前端展示失败原因。」

- **EN:** “Then we use Celery **automatic retry**, at most 3 times with **exponential backoff** (e.g. 1s, 2s, 4s) so we don’t hammer the LLM. If it still fails we leave it failed and **let the user click ‘Regenerate’ to run the task again**. In production we can also add alerts or a dead-letter queue for failed tasks.”  
  **中文：** 「然后交给 Celery **自动重试**，最多 3 次，间隔用 **指数退避**（例如 1 秒、2 秒、4 秒），避免连续打爆 LLM。若仍失败就保持 failed，**由用户点『重新生成』再发一次任务**；生产上还可以对失败任务做告警或进死信队列。」

这样既说了「重试 + 退避 + 状态 + 用户重新生成」，也带了「记错误、可告警」，面试官会觉得你考虑得比较全。  
*That covers retry, backoff, status, and user regeneration, plus recording errors and optional alerting — shows you’ve thought it through.*


# What if your worker can’t keep up？
The answer is, I would scale the workers horizontally and spin up more worker instances to work independently and pull tasks from the queue. Adding workers linearly increases throughput; the queue, the database, and the API service don't need to change.

For example:
1. One worker handles three tasks per minute.
2. I need to handle 12.
3. I run four workers.

# What if your worker cannot keep up?

My answer is that increasing workers horizontally (spinning up more worker instances) and adding workers linearly can increase throughput.

For example:
1. If one worker can handle 3 tasks per minute and I need to handle 12, I can put four workers into that.
2. This ensures that on the API service, the frontend, database, and backend cannot influence each other.


# What happens when your worker crashes?

My answer is that user-facing operations aren't affected:
1. The API still accepts requests and saves to the database.
2. Tasks stay in the queue waiting.
3. When the worker recovers, it picks up right where it left off.

No data is lost because we persist to the database before queuing. It is one of the key benefits of decoupling a worker from the API service.

# 面试官经常问 “What if the external API call fails?”。这不只是 LLM 的问题——任何调外部服务的地方都可能失败（支付、发短信、第三方数据）。你的回答模式都一样：自动重试 + 有上限 + 间隔递增 + 最终兜底

I configure automatic retries with exponential backoff:

1. First try after 1 second
2. Then 2 seconds
3. Then 4 seconds

After all 3 attempts have failed, the task is marked as failed in the database. The user will see a failure status and can manually trigger a retry.
I configure automatic retries with exponential backoff:
1. First retry after 1 second
2. Second retry after 2 seconds
3. Third retry after 4 seconds

After all three attempts fail, the status changes to Failed and is saved to the database. The user will see the failure status and can manually trigger a retry.