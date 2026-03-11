HTTP 的规则是：前端发请求，后端回响应。后端不能主动给前端发消息。

I have a question based on my system right now. I want to know about the different kinds of microservices and how they can communicate.

My Django setup sends a message to the database, the database sends a message to Redis, and Redis gives the data to Celery. Regarding the way of communication between Redis and Celery:
1. It is not polling; it is always in the waiting time.
2. They will wait for five seconds, and Redis sends the message to Celery.
3. Within these five seconds, Celery receives the message and knows they should take action to call the main process.

Since Celery is always in the waiting time, can Celery use the polling method instead? For example, every three seconds, Celery asks Redis, "Is there any task I need to do?"

I learned the different communication methods in Redis between Celery and the frontend, and between the frontend and the backend.

1. Redis and Celery
   In Redis, when communicating with Celery, I use the listening method via pub/sub or LPUSH/BRPOP. Celery is always in a waiting state; if Redis has a task, it sends it to Celery. If Celery is asleep, it wakes up the worker to finish the task.

   Actually, there is a mistake in how I described the communication between Redis and Celery. （上面一段是错的）

    The fact is, Celery effectively "hangs" on Redis (挂在 Redis 上). Celery puts itself on Redis, and Redis knows that someone is waiting. When work comes in, it is sent to the worker. I think that is the whole workflow.

2. Polling
   The other method is polling. Every three seconds, Celery asks Redis, "Is there any work I need to do?"

3. Frontend and Backend
   The difference between the frontend and backend is that because of the HTTP protocol, the backend cannot initiate a method to the frontend. Therefore, we need to use polling on the frontend. Every three seconds, the frontend asks Django, "Is my task finished?" Django receives this request, and the backend searches the database to see if the status is completed. If it is, Django returns the result to the frontend.



# Polling 与 Mock — 理解自检

---

## 1. 后端主动通知前端 vs 前端主动问后端，为什么我们只能选后者？

**你的回答 / Your answer**  
Because HTTP dictates that the frontend can only send requests to the backend; the backend cannot actively send messages to the frontend. So we can only choose polling (frontend asks backend for updates).

**判断与补充：**

- **对的部分**：在**单次 HTTP 请求-响应**里，确实是「前端发请求、后端回响应」；响应发出去之后，后端没法再通过这条连接主动推新数据。所以如果**只用普通 HTTP、不建长连接**，要让前端拿到「任务完成」的结果，只能靠前端**再发新请求**（轮询就是这种「隔一段时间发一次」的方式）。  
  所以：**在「只用 HTTP 且不建长连接」的前提下，确实只能选「前端主动问」这一类方式（例如 Polling）。**

- **可补充**：  
  - 我们**不是**「技术上只能选轮询」——还可以用 **WebSocket** 或 **Server-Sent Events (SSE)**：前端先发起一次请求并**保持连接**，之后后端可以在这条连接上**主动发消息**给前端。  
  - 所以更准确的说法是：  
    - **普通 HTTP**：后端不能主动推 → 要么轮询（前端反复问），要么前端再发新请求。  
    - **WebSocket/SSE**：后端可以主动推，但需要额外实现和维护长连接。  
  - 我们**选择**轮询，是因为实现简单、不需要 WebSocket/SSE 服务，而不是因为「协议只允许这一种方式」。

**面试一句（EN）：**  
“With plain HTTP, the server can’t push after the response is sent, so the client has to ask again—that’s polling. We could also use WebSocket or SSE for push, but we chose polling for simplicity.”

**面试一句（中文）：**  
「在普通 HTTP 下，后端不能在响应发完后再主动推数据，所以只能由前端反复请求，也就是轮询；也可以用 WebSocket/SSE 做主动推送，我们选轮询是因为实现更简单。」

---

## 2. Polling 的优点和缺点各是什么？

**你的回答 / Your answer**  
- Advantages: straightforward; after the answer is ready, the frontend can retrieve and show it.  
- Disadvantages: delay (e.g. answer ready at 0.1s but interval 3s → wait up to ~3s); improper interval can send too many requests and increase server load.

**判断：** 方向正确。✅

**可补充：**

- **优点**  
  - 实现简单，不需要额外组件（如 WebSocket 服务）。  
  - 和现有 HTTP API 兼容，任何后端都能支持。  
  - 行为容易理解和排查（每次就是一次 GET 请求）。

- **缺点**  
  - **延迟**：结果已经好了，用户也要等多至一个轮询间隔（如 3 秒）才看到，你举的例子对。  
  - **无效请求**：大部分请求可能都是「还没好」，造成一定浪费和服务器压力；间隔太短会放大这个问题。  
  - **扩展性**：用户很多、且轮询很频繁时，QPS 会上去，需要控制间隔或考虑 WebSocket/SSE。

**面试一句（EN）：**  
“Polling is simple and works with any HTTP API, but it adds delay (up to one interval) and can waste requests if the interval is too short.”

**面试一句（中文）：**  
「轮询实现简单、和现有接口兼容，但会有最多一个周期的延迟，间隔设不好还会多很多无效请求。」

---

## 3. Mock 的优点是什么？什么时候用真的 LLM，什么时候用 Mock？

**你的回答 / Your answer**  
Mock lets us use a fake LLM answer instead of calling the real one, saving **KPI (tokens)** and cost. Use real LLM when we want to verify if the LLM is truly useful; in test environment we always use mock.

**判断与修正：**

- **小笔误**：这里应是 **API (tokens)** 或直接说 **tokens / 费用**。**KPI** 一般指 Key Performance Indicator（关键绩效指标），和「省 token」不是同一个概念。

- **优点**：省 token、省成本、不依赖真实 API、响应快（几乎立刻返回），方便在本地/CI 里反复跑流程。✅

- **什么时候用真的 LLM**  
  - 生产环境（真实用户）。  
  - 要评估模型效果、改 prompt、调结构时。  
  - 有时在预发/测试环境也会短时间开真实 LLM，做端到端验证（可配合用量限制）。

- **什么时候用 Mock**  
  - 本地开发、CI、大部分自动化测试：不花钱、不等时、不依赖网络。  
  - 做演示或联调「除 LLM 以外」的流程（Worker、DB、前端轮询等）。  
  - “Test environment we **always** use mock” 可以改成 “**usually**” 或 “for most tests we use mock”，更贴切（因为 staging 有时会开真 API）。

**面试一句（EN）：**  
“We use a mock LLM to save API cost and avoid latency in dev and CI; we use the real LLM in production and when we need to evaluate output quality or prompt changes.”

**面试一句（中文）：**  
「Mock 用来在开发和测试里省费用、省时间；生产用真实 LLM，要评估效果或改 prompt 时也用真实 LLM。」



## API design
On the API design method: if I use polling, I need to add a new API in the backend. We should design a specific light status API to process this kind of request instead of using the very detailed API.


## Polling VS SSE
The polling method wastes requests, so do you have a better plan to address that?

I think we can use SSE. With polling, the client checks the status every 3 seconds, but the downside is wasting requests when the task isn't done yet. A more efficient alternative would be SSE, where the server pushes the result when it is ready.

However, polling was the right trade-off for our use case because:
1. It is simple to implement.
2. With only a few thousand concurrent users, the extra requests are negligible.