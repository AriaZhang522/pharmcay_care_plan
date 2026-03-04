# 后端文件说明：各自做什么、哪些需要重点看

一句话：**改业务逻辑时重点看「你的逻辑」那几个文件；其余当系统/胶水，只在改配置或跑命令时打开。**

---

## 1. 需要重点看的（你的业务逻辑）

| 文件 | 作用 | 什么时候看 |
|------|------|------------|
| **app/views.py** | 处理 HTTP：解析请求、调 DB/LLM、返回 JSON。 | 每次加/改接口或流程时。 |
| **app/models.py** | 表结构定义（Patient、Order、CarePlan 等）。 | 加/改表或字段时。 |
| **app/urls.py** | URL 和 view 的对应关系。 | 加/改接口路径时。 |

这三块就是「这个应用在做什么」的核心，其余要么是配置 Django，要么是跑命令、打镜像。

---

## 2. settings.py — **只管配置**（扫一眼即可，很少改）

**做什么：**  
告诉 Django 怎么跑：用哪个 app、连哪个库、CORS、用哪份 URL 配置、环境变量等。

**逻辑简述：**
- `ROOT_URLCONF = "app.urls"` → Django 从 `app/urls.py` 读路由。
- `INSTALLED_APPS` → 加载 `app` 包（以及 corsheaders、rest_framework）。
- `DATABASES` → 从环境变量读 `POSTGRES_*`（或默认值），用来连 PostgreSQL。
- `ANTHROPIC_API_KEY` → views 里用 `settings.ANTHROPIC_API_KEY` 调 LLM。

**要不要细看：** 知道「数据库和 API Key 从哪来」即可，以后只有加新配置（例如新环境变量）或改 DB/CORS 时再打开。

---

## 3. manage.py — **Django 入口脚本**（不用看）

**做什么：**  
所有 Django 命令都通过它跑：设置 `DJANGO_SETTINGS_MODULE` 为 `app.settings`，然后调 Django 自带的命令行。

**逻辑：**  
`python manage.py runserver` → 启动服务。  
`python manage.py migrate` → 执行迁移。  
`python manage.py load_mock_data` → 执行你的自定义命令。  
除非改项目名或 settings 模块名，否则不用动这个文件。

**要不要细看：** 不用，当系统自带的就行。

---

## 4. management/ — **自定义命令行命令**（只用到的命令才看）

**做什么：**  
Django 通过这里挂自定义命令，例如 `load_mock_data`。  
- `app/management/` 和 `app/management/commands/` 是约定好的目录结构。  
- `load_mock_data.py` 才是具体实现：执行 `python manage.py load_mock_data` 时，Django 会找到它并执行里面的 `handle()`。

**逻辑：**  
继承 `BaseCommand`、实现 `handle()` 是 Django 的标准写法。你的逻辑在 `handle()` 里用 `app.models` 创建 Patient/Order/CarePlan 等，不涉及 HTTP。

**要不要细看：**  
- **management/__init__.py**、**commands/__init__.py**：空文件，不用看。  
- **commands/load_mock_data.py**：只有改 mock 数据或加新命令时才需要看。

---

## 5. migrations/ — **数据库 schema 历史**（不用逐行看)

**做什么：**  
每个文件代表数据库的一个「版本」：建表、改列等。  
- Django 对比 **models.py**（当前想要的表结构）和 **migrations/**，在你执行 `makemigrations` 时生成新迁移。  
- 执行 `migrate` 时，Django 按顺序执行还没执行过的迁移，更新数据库。

**逻辑：**  
例如 `0001_initial_postgres.py` 表示「创建 patients、referring_providers、orders、care_plans 及字段、外键」。  
你的代码不会直接调用这些文件，是 `migrate` 命令在跑。

**要不要细看：**  
- 日常不用把 migrations 当代码去审。  
- 只有排查「为什么库和我想的不一样」或解决迁移冲突时才打开。  
- 改完 **models.py** 后，运行 `makemigrations` 生成新文件，再运行 `migrate`（本地或 Docker 里）应用即可。

---

## 6. Dockerfile — **后端镜像怎么构建**（改依赖或启动方式时扫一眼）

**做什么：**  
定义后端 Docker 镜像：基础镜像、用 `requirements.txt` 装依赖、拷贝代码、默认启动命令。

**逐行逻辑：**  
- `FROM python:3.11-slim` → 基础镜像。  
- `WORKDIR /app` → 容器内工作目录。  
- `COPY requirements.txt` + `RUN pip install` → 装 Python 依赖。  
- `COPY . .` → 拷贝整份代码。  
- `CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]` → 容器启动时默认执行的命令（在 docker-compose 里会被改成先 migrate 再 runserver）。

**要不要细看：** 只有加系统依赖、改 Python 版本或改启动方式时再看，这里没有业务逻辑。

---

## 7. 总结：要「审」的 vs 系统/胶水

| 类型 | 文件 | 建议 |
|------|------|------|
| **改行为时要审** | **app/views.py**、**app/models.py**、**app/urls.py** | 认真看、想清楚逻辑。 |
| **扫一眼，需要时再改** | **app/settings.py**、**Dockerfile** | 知道它们管什么配置/构建即可。 |
| **用到再看** | **app/management/commands/load_mock_data.py** | 改 mock 数据或加新命令时再看。 |
| **不用审** | **manage.py**、**app/management/__init__.py**、**app/management/commands/__init__.py**、**app/migrations/*.py** | 当系统/样板； migrations 用 `makemigrations` / `migrate` 操作即可，不必逐行读。 |

审代码时优先盯 **views.py → models.py → urls.py**，其余只在改配置、改运行/部署方式时再打开。
