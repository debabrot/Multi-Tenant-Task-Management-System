# Project Plan – step-by-step, smallest shippable slice first

## PLAN

### Phase 4 – Auth working slice

1. Security utilities (`core/security.py`)  
   • `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`.  
2. Service (`services/auth_service.py`)  
   • `register()` – insert user row.  
   • `login()` – verify password, return tokens.  
3. Update router functions to call service, return real 200/400.  
4. Test with curl or Swagger.

### Phase 5 – Current user info

1. Schema `UserOut` in `schemas/user.py`.  
2. Router `GET /me` that uses JWT dependency to get user id and returns `UserOut`.  
3. No update yet; just read.

### Phase 6 – Task CRUD skeleton

1. Schema `TaskCreate`, `TaskOut`, `TaskListOut` in `schemas/task.py`.  
2. Router `routers/tasks.py` – stub all endpoints with 501.  
3. Wire router.

### Phase 7 – Task CRUD working slice

1. Service (`services/task_service.py`)  
   • `create_task`, `list_tasks`, `get_task`, `update_task`, `delete_task`.  
2. Fill in router functions; protect with JWT dependency.  
3. Verify via Swagger.

### Phase 8 – Polish

1. Refresh & logout endpoints.  
2. PATCH /tasks/{id} and PATCH /me.  
3. Pagination (`utils/pagination.py`) and query filters.  
4. Soft delete flag if desired.  
5. Unit tests for services (optional but recommended).

Time guide
• Phase 1–2: 1–2 hours  
• Phase 3–4: 2–3 hours  
• Phase 5: 30 min  
• Phase 6–7: 3–4 hours  
• Phase 8: as much polish as you want

## DONE

### Phase 0 – One-time prep (single session, <30 min)

1. Create empty folders/files exactly as listed in the architecture.  
2. Keep them blank except for `__init__.py`.

### Phase 1 – Hello World (goal: container boots & returns 200)

1. In `main.py`  
   • write `create_app()` that returns a FastAPI instance.  
   • add one route `GET /ping` → `{"ping": "pong"}`  
2. `docker compose up` – verify http://localhost:8000/ping works.

### Phase 2 – DB & Migrations (goal: tables exist)

1. In `core/database.py`  
   • `DatabaseManager` with `engine`, `SessionLocal`, and `get_db()` dependency.  
2. In `core/config.py` add the missing DB URL env var.  
3. Run `alembic init migrations` (if not done) and generate first migration.  
4. `docker compose up` – confirm tables appear in Postgres.

### Phase 3 – Auth skeleton (goal: can register & login via Swagger)

1. Schemas  
   • write `RegisterRequest`, `LoginRequest`, `TokenResponse` in `schemas/auth.py`.  
2. Router  
   • `routers/auth.py` – stub two endpoints returning 501 “Not Implemented”.  
3. Wire router into `main.py`.  
4. Test in Swagger that endpoints appear.