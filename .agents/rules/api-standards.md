---
trigger: glob
globs: api/**/*.py
description: REST API Conventions, Pydantic Validation, & FastAPI Patterns
---

## 1. Strict Pydantic Validation
* **Rule:** Every API endpoint MUST use Pydantic models for both request and response validation. No `dict` or `Any` types in endpoint signatures.
* **Enforcement:**
  * Request bodies use Pydantic `BaseModel` with `Field()` constraints (min_length, max_length, ge, le, pattern).
  * Response bodies use Pydantic `BaseModel` with `model_config = {"from_attributes": True}` for ORM compatibility.
  * All schemas live in `api/app/schemas/` — never define inline Pydantic models in routers.

## 2. Dependency Injection Over Direct Imports
* **Rule:** Database sessions, configuration, and authentication MUST be injected via FastAPI's `Depends()` mechanism, never imported directly in routers.
* **Enforcement:** Use the `Annotated` type aliases defined in `api/app/dependencies.py`:
  * `DbSession` for database access
  * `AppSettings` for configuration
  * `AuthenticatedKey` for API key validation
  * New dependencies MUST be added to `dependencies.py` and used via `Depends()`.

## 3. REST Endpoint Conventions
* **Rule:** All API endpoints must follow consistent URL patterns and HTTP semantics.
* **Enforcement:**
  * Prefix all endpoints with `/api/v1/` for API versioning.
  * Use plural nouns for resources: `/briefings`, `/accounts`, `/chat/sessions`.
  * `POST` for creation and actions, `GET` for retrieval, `PATCH` for partial updates, `DELETE` for removal.
  * Return `200` for success, `201` for creation, `404` for not found, `422` for validation errors, `500` for server errors.
  * Always return JSON — never return plain text or HTML from API endpoints.

## 4. Error Response Format
* **Rule:** All error responses must follow a consistent JSON structure.
* **Enforcement:** Use FastAPI's `HTTPException` with structured `detail`:
  ```python
  raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Account not found for the given external_id."
  )
  ```
  The global exception handler in `middleware/error_handler.py` catches unhandled exceptions and returns `{"detail": "...", "type": "internal_error"}`. Stack traces are NEVER exposed to clients.

## 5. Async-First
* **Rule:** All database operations and external API calls MUST use async/await.
* **Enforcement:** Use `async def` for all route handlers and service methods. Use `AsyncSession` for database queries. Use `asyncio.create_task()` for fire-and-forget operations like usage logging. Never use synchronous `requests` library — use `httpx` for any HTTP calls not covered by the Vertex AI SDK.

## 6. SQLAlchemy ORM Patterns
* **Rule:** All database access MUST go through SQLAlchemy ORM models. No raw SQL strings in application code (migrations are the exception).
* **Enforcement:**
  * Use `select()` construct for queries, never string-based queries.
  * Use `db.flush()` + `db.refresh()` after inserts to get server-generated values (UUIDs, timestamps).
  * Use `session.commit()` lifecycle managed by the `get_db()` dependency — never commit manually in service code.
