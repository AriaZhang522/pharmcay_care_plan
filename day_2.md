1. Frontend -> API -> Backend

- POST: "Here is new information"Direction: Front-end (with data) $\rightarrow$ API $\rightarrow$ Back-end saves it.


- GET: "Give me information"Direction: Front-end $\rightarrow$ asks API $\rightarrow$ Back-end sends data back.

here user is in the front end. if i want to get info from backend, backend sent info to me -> this is get.

If i want to send info to backend, this is post

## question 4 --- the process is walkthrough, which i should do when interviewing
in the first time, i cannot answer this question.  if i have two api design, but i dn;t have any code, how can i know whether can i use this api.

the answer is : you say the whole process.
firstly i fill the form and click the sumbit button, and the post api start to work, it send my form to backend, waits for 10 sec, the backend say oh, done, the order number is 123 and here is your care plan:

secondly, several days later, i want to see the order whose number is 123, and i call the get api with order number 123, so backend send me the care plan.


my api key: (store in .env locally, do not commit)
name: pharmacy_career_plan



github can detect the real API key in order to avoid revealing

if I change frontend and backend code, i need to rebuild and restart docker to make the new code work.
terminal command line is : `cd /Users/zhangyuyan/Desktop/pharmacy_career_plan/careplan-mvp && docker compose build frontend && docker compose up -d frontend`

if i change the code and want to push the code to github, i need to 
```
cd /Users/zhangyuyan/Desktop/pharmacy_career_plan

# 新建并切换到新分支（把 branch_name 换成你要的名字，例如 mvp_v1.1）
git checkout -b branch_name

# 添加所有改动
git add .

# 提交
git commit -m "你的提交说明"

# 推送到远程并设置上游（第一次推这个分支时用）
git push -u origin branch_name
```




# Debugging

## changes of enviroments

## Frontend
Firstly, open chrome and find the local host 5173, then click `f12`, open source and click pages to find APP.jsx to debug. then find the handlesumbit function,(why find this function?because when click generate cae plan, the only function it will call is handlesumbit. from the dataflow perspective, `fetch`send request to handlesumbit, when get the result, setresult/ seterror will work, when laoding, setloading will work, if still loading, the status is true, which will forbidden users to click the `generate care plan button` )

# Test
我今天学了 API 设计、同步调用 LLM、Docker。现在我把我的理解讲给你，你帮我判断有没有差错，或者可以补充的地方。

1. 我们的系统为什么需要 POST 和 GET 两个 API？一个 API 搞定行不行？
2. 用户点提交后要等 10-20 秒，这个同步调用有什么问题？我能想到哪些？
3. Docker 在这个项目里帮我做了什么？如果不用 Docker 会怎样？
4. 我的 POST 请求从前端发出后，经过了哪些步骤，最后怎么返回给前端的？

我的回答是：
1. post and get is from the users' perspective. Post is user send info to backend, which means when users use front end to type in info, call the post api to send the info to backend. and get api is when backend get AI's answer and get a care plan, call get api to send the answer to front end. so we need two kind of api post and get. 

2. the second question is what i am confused. if we we call it 'sync', we should get the ai's answer ASAP. it is too slow and if there are servel people entering info at the same time, there are too much question waiting for ai to answer, it  will be slower. 

3. docker put all the environment doc as a package. and i don't need to install the packages in my pc, only put it in docker. if i want to send the environment to other people, i just send the docker package and code so that the other people don't need to install environment. if i don't use docker, i need to install requirments.txt into virtual environment. 

4. after click generate care plan button, post api works, firstly setloading status change from false into true, then backend receive the patient info and save it into dict. then backend read prompts line by line then call llm function, send the patient info and prompt to llm. then llm answer the question. backend receive the answer and change it into dict. then send the answer to front end.


*1. 为什么需要 POST 和 GET？一个 API 行不行？*

需要修正的一点：
当前流程里，AI 的 care plan 并不是通过 GET 给前端的。
用户点「Generate Care Plan」后：
前端发 POST，带表单数据。

后端在同一次 POST 里：收数据 → 调 LLM → 存进 ORDERS → 直接在同一次 POST 的响应里返回 order_id 和 care_plan。
`前端收到这份 POST 的 response 后 setResult，页面就显示 care plan。`

`所以「把 AI 的答案送到前端」是在 POST 的响应里完成的，没有再用 GET 去取这次刚生成的结果。}`

GET 的用途是另一件事：
按 order_id 查一条已经存在的订单（例如之后想重新打开某条、或通过链接分享）。所以：
POST：提交表单 → 创建订单 + 调 LLM → 在同一次响应里把 care plan 和 order_id 返回给前端。


GET：根据 order_id 查询之前已经生成好的订单（不负责「这次提交」的返回）。


一个 API 能不能搞定？
可以设计成「POST 只返回 order_id，前端再 GET 取结果」，但就要做轮询或等用户再点「查看」，你现在的设计是「POST 一次等到底、一次拿到结果」，更简单。所以需要两个 API 是因为职责不同：一个负责「创建并返回当次结果」，一个负责「按 id 查已有结果」。

* 2. 同步调用等 10–20 秒有什么问题？*

“Sync” 不是“快”的意思：
Sync = 请求会一直卡住，直到 LLM 返回才回复，连接一直占着。所以「同步」反而更容易让人等很久，你的担心对。
你已经说到的：
要等 10–20 秒，体验差。
多人同时提交时，请求排队等 AI，会更慢。

可以再补充的：
- 超时：浏览器或反向代理常有 30–60 秒超时，LLM 再慢一点就可能断掉，用户看到失败。
- 占用资源：每个请求在等 LLM 的这段时间都占着一个 worker/线程，人一多就要很多 worker，成本高。
- 体验：长时间转圈用户可能以为坏了、刷新或重复点，造成重复提交。
- 不能取消：一旦发了请求，没法中途取消或只查「做到哪一步了」。

改进方向一般是：做成异步（POST 先返回「已受理」，前端轮询或用 WebSocket 取结果），这样连接不会长时间挂着，超时和并发会好很多。

*3. Docker 在这个项目里做了什么？不用会怎样？*

你理解得对：
把运行环境（Python、依赖、Node、前端依赖）打成一个可复现的「包」；别人拿到镜像/ compose 就能跑，不用自己装 Python/Node、配 venv、npm install。

可以补充的：
- 环境一致：大家跑的都是同一套系统（同一 Python/Node 版本、同一依赖），减少「在我机器上能跑在你机器上不行」。
- 一键起服务：docker compose up 同时起后端和前端，不用开两个终端、记两条命令。

不用 Docker 时：就要在本机装 Python、Node，自己建 venv、pip install -r requirements.txt、npm install，再分别起 backend 和 frontend；别人环境不同就可能遇到版本问题。

*4. POST 从前端发出后，经过了哪些步骤，最后怎么返回给前端？*

整体顺序你对，有几处可以更精确：
- setLoading：点击后先把 loading 设为 true（表示「请求进行中」），不是 false→true 写反就成。

- 后端：收到 POST body → 解析 JSON 成 body → 用 body 组出 order 字典（此时 care_plan 还是 None）→ 调 call_llm_for_care_plan(order)，把一整段 prompt（已经用 order 填好的模板）发给 LLM → LLM 返回一段文本 → 后端解析成 dict 赋给 order["care_plan"] → 执行 ORDERS[order_id] = order 存起来 → 立刻 return JsonResponse({ "order_id": ..., "care_plan": ... })。

- “最后怎么返回给前端”：就是这次 POST 的 HTTP 响应把 order_id 和 care_plan 带回去；前端的 fetch 收到后 res.json() 得到 data，再 setResult({ care_plan: data.care_plan, order_id: data.order_id, orderInfo: form })、setLoading(false)，页面就显示结果。没有在「提交」这条链路里再发一次 GET；GET 是给「之后用 order_id 再查」用的。

把「AI 的答案是通过 POST 的响应一次返回的，不是通过 GET」这一点补进你的第 1 和第 4 点，你的理解就基本完整、没有大错了。