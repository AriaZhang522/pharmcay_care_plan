# problems

1. I found that I have problems with building database structure.

2. How to address the duplicate problems?
set the key which is always the same as the first layer. the unstable key should be put in the second layer.


I need to organize my thoughts to make me more understand this project's whole sturcture.

firstly, about debugging. if i want to debug on my pc, i should create a virtual environment to install the packages into that. and open two terminals, one frontend, another backend. and use n / p this kind of command to debug.

But if i just want to run the code in docker, I can execute the code - docker compose up if i want to close it, i run the code docker compose down.




secondly about database. Because If I only use python memory to store the data, when i kill the docker process, the data will miss. So I use database to store data, also don't use frontend to call the data, because i think it is a criteria in tech industry, give the press to api layer not the database layer. In API layer, we can control the speed of  processing the message queue, we can do load balancer, cache, rate limiting.

How to increase the speed when I/O?


## The whole structure of data flow direction

- 用户在前端填数据，点 “Generate Care Plan”。
- 前端发 POST 到 /api/generate-care-plan/。
- Django 收到请求，urls.py 根据这个 URL 把请求路由到 views.generate_care_plan，Django 调用 views.generate_care_plan(request)。
- views.py 解析 request 里的数据，通过 models.py 里的模型（Patient、ReferringProvider、Order、CarePlan）把数据写入数据库；表结构是你设计的，由 migrations 建表。
- 数据写库后，views.py 调用 call_llm_for_care_plan，用你在代码里写的 prompt 调 AI。
- 拿到 AI 的答案后，后端把结果写回数据库（更新 CarePlan），再 return 前端需要的数据（order_id、care_plan 等）给前端。
- 所以：除了“urls.py 是路由、真正接请求并干活的是 views.py”这一点，你整条 POST 流程的理解是对的。



# testing

我今天学了数据库设计，把项目从内存存储升级成了 PostgreSQL。现在我把我的理解讲给你，你帮我判断有没有差错，或者可以补充的地方。

1. 为什么不能把所有数据都塞进一个表？拆成多个表解决了什么问题？
2. 外键是什么？在我们这个项目里，哪些表之间有外键关系？
3. 为什么用 PostgreSQL 而不是 SQLite？如果面试官问我"为什么不用 MongoDB"，我该怎么回答？
4. 为什么不让用户直接连数据库查数据，而是要通过 API？
5. Care Plan 的状态（pending → processing → completed / failed）有什么用？为什么内存存储的时候不需要这个？

我的回答是：1. if putting all the data into a whole table, when i want to change one patient's name or dob, it will change several records. if i spilt it into several subtables, each table has a external key mapping to another, so if i change one key of one record of one table, i only change one record. this is decoupling. 2. external key is the key to interact with another table.  one patient has many orders, one provider has many orders, one order has one care plan. patient with order, provider with order, order with care plan. 3. PostgrSQL is the true relational database, SQLite is a file , it don't occupy port and don't pair user. Mongo DB is unrelational database, the info stored at MongoDB is unstructured, but in our task, our data has a standard structure, and easy to maintain。 4. If users connect to database to search info, when the user write a wrong code, some horrible thing like deleting all data or deleting very important data or data leakage might occur.  and using API we can do load balancer rate limiting, it is like a barrier standing between user and date, to protect the data security and improve the experience for users. 5. care plan status can help backend to understand the status of data, because when we save the data to database, this is a step that don't occur in memory storage way, so we need to determine whether the data is stored properly, and because when the number of users increase, if there are several users waiting for get the careplan, the status is pending.  
# 数据库设计理解自检（面试可答版）

## 1. 为什么不能把所有数据塞进一个表？拆成多个表解决了什么问题？

**要点：**
- 若所有数据塞进一张表，改一个病人的名字或 DOB 就要改多条记录；拆成多表后，每个表用外键关联，改一条只动一处，解耦。
- **可补充：**
  - **去冗余 reduce redundancy **：同一病人多笔订单时，病人姓名、MRN 只存一份（patients 表），不会在每笔订单里重复。
  - **单一事实来源 only fact source**：病人信息只在一个地方维护，不会出现「这笔订单名字对、那笔写错」的不一致。
  - 面试可说：**拆表 = 规范化（normalization）+ 减少冗余 + 更新只改一处 The update only changes one place。**

---

## 2. 外键是什么？在我们这个项目里，哪些表之间有外键关系？

**要点：**
- 外键（**foreign key**）是和另一张表关联的键，用来表达表与表之间的关系。
- 本项目：一个病人多笔订单、一个医生多笔订单、一个订单对应一个 Care Plan。即：Patient ↔ Order、ReferringProvider ↔ Order、Order ↔ CarePlan。

**本项目具体关系：**
- **orders 表**：有 `patient_id`（→ patients）、`referring_provider_id`（→ referring_providers）。
- **care_plans 表**：有 `order_id`（→ orders，且是 OneToOne，一个订单对应一个 care plan）。

---

## 3. 为什么用 PostgreSQL 而不是 SQLite？如果面试官问「为什么不用 MongoDB」怎么答？

**PostgreSQL vs SQLite：**
- PostgreSQL 是真正的关系型数据库 relational database 服务；SQLite 是单文件，不占端口、不配用户，适合本地/小工具。
- **可补充**：多用户、并发写、要部署到服务器时，PostgreSQL 更合适，支持多连接、事务、备份，生产环境常用。

**为什么不用 MongoDB：**
- MongoDB 是非关系型non relational database（文档型），存的是非结构化/半结构化数据；我们业务里数据有固定结构（病人、订单、Care Plan），用关系型更好维护。
- **可补充**：我们数据是强关系（病人→订单→Care Plan），需要关联查询、外键约束、事务（ACID），关系型更自然；MongoDB 适合 schema 灵活、文档型场景。面试可说：**「我们业务是典型的关系型数据，需要关联和事务，所以选 PostgreSQL；MongoDB 更适合 schema 灵活、文档型的场景。」**

---

## 4. 为什么不让用户直接连数据库查数据，而是要通过 API？

**要点：**
- 若用户直连数据库，一旦写错代码可能误删/误改重要数据或造成数据泄露；用 API 可以做负载均衡、限流，相当于在用户和数据库之间加一层，保护数据、也能提升体验。

**可补充：**
- **权限**：API 能按「谁登录、什么角色」控制能查/改什么；直连就要发数据库账号密码，权限难细粒度控制。
- **业务逻辑集中**：校验（如 mrn、npi 必填）、规则都写在 API 里；直连则逻辑散落在各客户端。
- **审计**：API 可记录「谁在什么时候调了哪个接口」，方便排查和合规。

---

## 5. Care Plan 的状态（pending → processing → completed / failed）有什么用？为什么内存存储时不需要？

**要点：**
- 状态让后端知道当前这笔数据处在哪一阶段；存库是多出来的一步，需要确认是否存好；用户多时有人排队就是 pending。

**可补充：**
- **持久化 data persistence**：内存里请求在处理时，结果和状态都在同一进程，请求结束就没了。数据库是持久存储，请求可能超时、服务器可能重启，或用户刷新页面——需要靠**库里存的状态**知道这笔订单是处理中、已完成还是失败，所以要在 DB 里记 pending / processing / completed / failed。
- **用户体验**：前端可根据 status 显示「处理中…」「生成失败，请重试」。
- **以后扩展**：若改成异步任务队列，worker 扫 status=pending 的订单去调 LLM，status 就是任务状态，方便重试和监控。

**一句话**：内存存储时「处理中」只是当前请求的临时状态，不落库；用数据库后要把「进行到哪一步」持久化下来，所以需要 status 字段。