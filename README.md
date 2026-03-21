# CareForge — AI-Powered Specialty Pharmacy Care Plan System

> An end-to-end prototype for automated pharmacy care plan generation, built with async-first architecture, LLM orchestration, and production-grade tooling.

---

## Overview

CareForge automates the full lifecycle of specialty pharmacy care plan generation — from multi-source order intake to AI-generated clinical documents. It eliminates manual documentation overhead, enforces data quality at ingestion, and delivers consistent, clinician-ready care plans at scale.

---

## Features

### Clinical Workflow
- **Web-based order intake** — Submit patient information, medications, and diagnoses via an interactive React UI
- **Duplicate detection** — Automatic deduplication of patients and orders at ingestion
- **LLM-powered care plan generation** — Structured patient data is processed by an LLM service to generate professional care plan documents
- **Document download** — Generated care plans are immediately available for download
- **Data export** — Bulk export support for reporting and compliance workflows
- **Multi-source order ingestion** — Adapter pattern normalizes orders from heterogeneous upstream systems (web form, EHR, fax, API, etc.)

### Engineering Architecture
- **Async task processing** — Celery + Redis offloads LLM calls to background workers, keeping the API non-blocking
- **Business validation layer** — Complex clinical validation enforced before any downstream processing
- **Adapter pattern** — Unified ingestion interface decouples input sources from core business logic
- **Containerized deployment** — One-command local startup via Docker Compose
- **Cloud infrastructure** — AWS deployment managed via Terraform (ECS, RDS, S3, VPC)
- **Observability** — Prometheus + Grafana for real-time monitoring of queue depth, LLM latency, and error rates

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3, Django, Django REST Framework |
| Task Queue | Celery + Redis |
| Database | PostgreSQL |
| LLM Integration | `app/llm.py` + `app/services.py` abstraction layer |
| Frontend | React + Vite |
| Containerization | Docker, Docker Compose |
| Cloud Infrastructure | AWS (ECS, RDS, S3, VPC) |
| Infrastructure as Code | Terraform |
| Monitoring | Prometheus + Grafana |

---

## System Architecture

```
                    ┌─────────────────────────────────────┐
                    │           Upstream Sources           │
                    │   (Web Form / EHR / Fax / API)      │
                    └──────────────┬──────────────────────┘
                                   │
                            Adapter Layer
                     (normalizes all input formats)
                                   │
                    ┌──────────────▼──────────────────────┐
                    │         Django REST API              │
                    │  • Business validation               │
                    │  • Duplicate detection               │
                    │  • Order persistence (PostgreSQL)    │
                    └──────────────┬──────────────────────┘
                                   │
                        Async Task Queue
                         (Celery + Redis)
                                   │
                    ┌──────────────▼──────────────────────┐
                    │          Celery Worker               │
                    │  • LLM call (care plan generation)   │
                    │  • Document storage                  │
                    │  • Status update                     │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │     Monitoring & Observability       │
                    │       Prometheus + Grafana           │
                    └─────────────────────────────────────┘
```

---

## Project Structure

```
.
├── design_doc.md
├── careplan-mvp/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── models.py          # Patient, Order, CarePlan data models
│   │   │   ├── serializers.py     # DRF serializers
│   │   │   ├── views.py           # API endpoint handlers
│   │   │   ├── tasks.py           # Celery async tasks
│   │   │   ├── services.py        # Business logic layer
│   │   │   ├── llm.py             # LLM service orchestration
│   │   │   ├── celery.py          # Celery app configuration
│   │   │   ├── settings.py        # Django settings
│   │   │   ├── migrations/
│   │   │   │   └── 0001_initial_postgres.py
│   │   │   └── management/
│   │   │       └── commands/
│   │   │           ├── load_mock_data.py
│   │   │           └── run_care_plan_worker.py
│   │   ├── manage.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── mock_data.sql
│   │   └── docker-compose.yml
│   └── frontend/
│       ├── index.html
│       ├── package.json
│       ├── vite.config.js
│       └── src/
│           ├── App.jsx            # Main React SPA
│           └── main.jsx
```

---

## Quick Start

### Prerequisites
- Docker + Docker Compose

### Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/AriaZhang522/pharmcay_care_plan.git

# 2. Enter project folder
cd pharmcay_care_plan/careplan-mvp

# 3. Build and start all services
docker-compose up --build
```

### Access the App

| Service | URL |
|---------|-----|
| Frontend (React) | http://localhost:5173 |
| Backend API (Django) | http://localhost:8000 |

### Load Mock Data (Optional)

```bash
docker exec -it <backend_container> python manage.py load_mock_data
```

### Run Celery Worker Manually (if not in Compose)

```bash
python manage.py run_care_plan_worker
```

---

## Docker Compose Services

| Service | Description |
|---------|-------------|
| `backend` | Django REST API server |
| `frontend` | React + Vite dev server |
| `db` | PostgreSQL database |
| `worker` | Celery async worker for LLM tasks |
| `redis` | Message broker for Celery |

---

## Development Roadmap

| Version | Focus | Status |
|---------|-------|--------|
| v1 — Synchronous MVP | Web form + LLM + download, single-process | ✅ Complete |
| v2 — Persistent Storage | PostgreSQL, duplicate detection, data export | ✅ Complete |
| v3 — Async Architecture | Celery + Redis workers, non-blocking LLM calls | ✅ Complete |
| v4 — Multi-Source Ingestion | Adapter pattern, heterogeneous order sources | ✅ Complete |
| v5 — Cloud & Observability | Docker, Terraform/AWS, Prometheus + Grafana | 🔧 In Progress |

---

## Future Improvements

- [ ] Authentication and user role management
- [ ] Refined LLM prompt engineering and output quality
- [ ] Unit and integration test coverage
- [ ] CI/CD pipeline
- [ ] OpenAPI / Swagger documentation
- [ ] Pagination and filtering for care plan history
- [ ] Enhanced UI and error handling

---

## Notes

- `design_doc.md` and `learning_path/` are local design and learning artifacts
- `learning_path/` is excluded from version control via `.gitignore`
- To stop tracking `learning_path` if previously committed:

```bash
git rm -r --cached learning_path/
git commit -m "Stop tracking learning_path"
git push
```
