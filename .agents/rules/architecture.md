---
trigger: always_on
description: Monorepo Architecture, DRY Principle, & Service-Layer Separation
---

## 1. The DRY Principle
* **Rule:** Never duplicate logic. Apply the Rule of Three — if logic appears in two places, consider abstraction; if it appears in three, mandate it.
* **Enforcement:** Extract shared logic into dedicated utility or service modules:
  * `api/app/utils/` for backend utilities
  * `api/app/services/` for business logic
  * `intelligence/shared/` for cross-agent utilities
  * Inline helpers within the same file are acceptable only if the logic is tightly coupled and file-specific.

## 2. Single Responsibility & File Size
* **Rule:** Each file should have a single, well-defined responsibility.
* **Enforcement:** Source files should aim for ≤200 lines. Any file exceeding 300 lines MUST be aggressively refactored. Exceptions are allowed only for auto-generated files (e.g., Alembic migrations).

## 3. The Thin Transport Rule
* **Rule:** FastAPI route handlers in `api/app/routers/` are strictly transport layers. They parse the HTTP request, call a service, and return the response.
* **Enforcement:** Business logic, database queries, data transformation, AI orchestration, and validation belong in `api/app/services/`. Route handlers must never exceed 30 lines of logic — if they do, extract into a service. The handler's only job: validate input, call service, return output.

## 4. Three-Tier Layer Isolation
* **Rule:** The monorepo enforces strict layer boundaries. Cross-layer imports are prohibited.
* **Enforcement:**
  * `clients/` (Tier 1 — Presentation) MUST NEVER import from `api/` or `intelligence/`.
  * `api/` (Tier 2 — Core API) communicates with `intelligence/` (Tier 3) ONLY via the Vertex AI SDK or HTTP. No direct Python imports across these boundaries.
  * Each tier has its own `requirements.txt`, `Dockerfile`, and `README.md`.

## 5. Monorepo Directory Discipline
* **Rule:** Follow the directory layout defined in the System Architecture Spec.
* **Enforcement:**
  * `api/app/routers/` — FastAPI route handlers only
  * `api/app/services/` — Business logic only
  * `api/app/models/` — SQLAlchemy ORM models only
  * `api/app/schemas/` — Pydantic request/response models only
  * `api/app/middleware/` — Auth, rate limiting, error handling
  * `api/app/utils/` — Shared utilities
  * `intelligence/agents/` — Vertex AI agent classes
  * `intelligence/shared/` — Cross-agent utilities
  * `clients/` — Frontend-specific code, each in its own subdirectory
  * Never place source code outside the declared directories.

## 6. Configuration as Code
* **Rule:** All application configuration must be centralized in `api/app/config.py` using Pydantic Settings.
* **Enforcement:** No magic strings scattered across route handlers or services. Config values are read from environment variables with sane defaults. The `platform_config` database table is used for runtime-changeable values; `config.py` is for infrastructure-level settings.
