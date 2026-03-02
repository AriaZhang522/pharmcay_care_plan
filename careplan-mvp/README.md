# Care Plan MVP

最小可跑通的 care plan 生成系统。  
前端 React + 后端 Django + Claude AI，数据存在内存里，没有数据库。

## 目录结构

```
careplan-mvp/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   └── app/
│       ├── settings.py   ← Django 配置
│       ├── urls.py        ← 路由
│       └── views.py       ← 所有业务逻辑 + 内存存储
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        └── App.jsx        ← 所有 UI 逻辑
```

## 快速启动

### 1. 设置 API Key

```bash
# 在项目根目录创建 .env 文件
echo "ANTHROPIC_API_KEY=sk-ant-xxxx" > .env
```

### 2. 启动

```bash
cd careplan-mvp
docker-compose up --build
```

### 3. 打开浏览器

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000

## API

### POST /api/generate-care-plan/

请求 body (JSON):
```json
{
  "patient_first_name": "Jane",
  "patient_last_name": "Smith",
  "patient_mrn": "001234",
  "referring_provider": "Dr. Chen",
  "referring_provider_npi": "1234567890",
  "primary_diagnosis": "G70.01",
  "additional_diagnoses": ["I10", "K21.0"],
  "medication_name": "IVIG",
  "medication_history": ["Pyridostigmine 60mg q6h"],
  "patient_records": "Patient presents with..."
}
```

响应:
```json
{
  "order_id": "uuid-...",
  "care_plan": {
    "problem_list": ["..."],
    "goals": ["..."],
    "pharmacist_interventions": ["..."],
    "monitoring_plan": ["..."]
  }
}
```

### GET /api/orders/

返回所有已生成的订单列表（内存中）。

## 已知限制（MVP 故意不做的）

- 重启后数据消失（没有数据库）
- 没有重复检测（ERROR / WARNING）
- 没有输入验证
- 同步调用 LLM（用户等待 10-20 秒）
- 没有身份认证
- 没有错误重试

这些限制都是下一步要逐步加上的。
