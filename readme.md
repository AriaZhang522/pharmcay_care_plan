

# Pharmacy Career Plan 

## Project Summary

`pharmacy_care_plan` is a minimum viable product (MVP) that provides an end-to-end prototype for pharmacy career plan generation and management.

Key behaviors:
- Intake sample order data
- Backend computes a care plan using LLM-like service
- Task queue handles asynchronous processing (Celery)
- Frontend interactive UI for request + display
- Containerized local deployment (Docker Compose)

---

## Tech Stack

### Backend
- Python 3 + Django
- Django REST Framework
- PostgreSQL
- Celery + Redis
- Dockerfile + docker-compose.yml
- App core:
  - `app/models.py`
  - `app/serializers.py`
  - `app/views.py`
  - `app/tasks.py`
  - `app/services.py`
  - `app/llm.py`
  - `app/celery.py`
  - `app/settings.py`
  - `app/management/commands` (`load_mock_data`, `run_care_plan_worker`)
- Migrations:
  - `app/migrations/0001_initial_postgres.py`
- Mock data:
  - `mock_data.sql`

### Frontend
- React + Vite
- `frontend/src/App.jsx`
- `frontend/src/main.jsx`
- `frontend/vite.config.js`

### Dev tooling
- Docker Compose orchestrates:
  - backend
  - frontend
  - database (PostgreSQL)
  - worker (Celery)
- .gitignore includes environment and build artifacts, and now learning_path
- `backend/requirements.txt`
- `frontend/package.json`

---

## Architecture

```
.
├── design_doc.md
├── careplan-mvp/
│   ├─ backend/
│   │  ├─ app/
│   │  ├─ manage.py
│   │  ├─ Dockerfile
│   │  ├─ requirements.txt
│   │  ├─ mock_data.sql
│   │  ├─ docker-compose.yml
│   ├─ frontend/
│   │  ├─ index.html
│   │  ├─ package.json
│   │  ├─ vite.config.js
│   │  ├─ src/
│   │

```

---

## Features Delivered

1. API endpoints for care plan lifecycle.
2. DB model, migrations, and mock data seed.
3. Celery worker for asynchronous plan generation.
4. LLM service orchestration (`app/llm.py` + `app/services.py` abstraction).
5. React SPA for plan request and result display.
6. Containerized one-command startup:
   - `docker-compose up --build`

---

## Setup & Run

1. Clone repo:
   - `git clone https://github.com/AriaZhang522/pharmacy_care_plan.git`
2. Enter folder:
   - `cd pharmacy_care_plan/careplan-mvp`
3. Build and run:
   - `docker-compose up --build`
4. Visit:
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:5173`
5. Optional Django command:
   - `docker exec -it <backend_container> python manage.py load_mock_data`
6. Celery worker command (if not part of compose):
   - `python manage.py run_care_plan_worker`

---

## Git behavior and learning_path policy

- Local learning notes are in learning_path.
- .gitignore includes learning_path.
- Remove tracking in repo:
  - `git rm -r --cached learning_path/`
  - `git commit -m "Stop tracking learning_path"`
  - `git push`
- Local learning_path remains available and safe.

---

## Improvements (future)

- Add authentication and user roles.
- Refine LLM prompt and result quality.
- Add unit/integration tests.
- Add CI pipeline.
- Add API doc and schema (OpenAPI, Swagger).
- Add pagination and filtering for plan history.
- Add better UI and error handling.

---

## Notes

- design_doc.md and learning_path are for design and learning artifact purposes.
- Ensure correct Git remote as `https://github.com/AriaZhang522/pharmacy_care_plan.git`.

---

This README is tailored to what’s currently in your project and the state you described; you can paste this into `README.md` in repo root and update later with API details as the application evolves.