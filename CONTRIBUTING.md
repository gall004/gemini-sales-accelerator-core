# Contributing to Gemini Sales Accelerator Core

## Development Environment

### Prerequisites
- Docker Desktop ≥ 4.x
- Python 3.12+ (IDE support)
- Git ≥ 2.x

### Setup
```bash
git clone https://github.com/gall004/gemini-sales-accelerator-core.git
cd gemini-sales-accelerator-core
cp api/.env.example api/.env
docker compose up
```

The API runs at `http://localhost:8000` with hot-reload enabled.

## Git Workflow

### Branch Strategy
- **Never push directly to `main`.** All changes go through Pull Requests.
- Create feature branches from `main`: `feat/<scope>-<description>`
- Create fix branches from `main`: `fix/<scope>-<description>`

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(api): add briefing service endpoint
fix(sheets): handle empty company name
chore(infra): update docker-compose healthcheck
refactor(api): extract upsert logic to service
test(api): add briefing cache hit test
docs(api): update README with new endpoint
```

Standard scopes: `api`, `intelligence`, `sheets`, `infra`, `docs`

## Coding Standards

### Architecture Rules
- **Thin Transports:** Route handlers must be ≤30 lines. Business logic lives in `api/app/services/`.
- **DI Only:** Use `Depends()` for DB sessions, settings, auth — never import directly.
- **Async-First:** All handlers and service methods use `async def`.
- **File Size:** Source files aim for ≤200 lines, must be ≤300 lines.

### Configuration
- All config in `api/app/config.py` via Pydantic Settings.
- No hardcoded secrets, project IDs, or API keys.
- New env vars require simultaneous updates to: `.env.example`, `config.py`, `docker-compose.yml`, `README.md`.

### Logging
- Use `logging` module — never bare `print()`.
- Every `try/except` must log before re-raising.
- No silent exception swallowing.

### Docstrings
- Every public class and function must have a Google-style docstring.

## Testing

### TDD Mandate
1. Write a failing test first (Red).
2. Write implementation to pass it (Green).
3. Refactor as needed.

### Running Tests
```bash
# All tests with coverage
docker compose exec api pytest tests/ --cov=app --cov-report=term-missing -v

# Schema tests only (no DB)
docker compose exec api pytest tests/test_schemas.py -v
```

### Coverage Target
≥85% aggregate coverage across `api/app/`.

### Sad-Path Tests Required
For every endpoint/service, write tests for:
- Invalid input (missing fields, bad values)
- External service failure
- Authentication failure (missing/invalid API key)
- Error response structure verification

### Test Database
Tests use `gsa_core_test` (created once):
```bash
docker compose exec postgres psql -U gsa_user -d postgres -c "CREATE DATABASE gsa_core_test OWNER gsa_user;"
```

### Mock External Services
Tests must NEVER make real HTTP calls. Use `unittest.mock.patch` for Vertex AI, Google APIs, etc.

## Pull Request Process

1. **Branch** from `main` on a feature branch.
2. **Code** following architecture and testing standards.
3. **Test** — all tests must pass, coverage ≥85%.
4. **Pre-Flight Checklist:**
   - [ ] No `print()` or bare `logger.debug()` calls
   - [ ] No hardcoded secrets or GCP project IDs
   - [ ] No commented-out code blocks
   - [ ] No `.env` files staged
   - [ ] All tests pass
   - [ ] Coverage ≥85%
5. **Documentation Gate:** Update affected docs per the trigger matrix in `.agents/workflows/sdlc-workflow.md`.
6. **Push** and create a PR — do not merge without review.

## Directory Layout

```
api/app/
├── config.py       # Pydantic Settings
├── database.py     # Async engine & session factory
├── dependencies.py # FastAPI DI (DbSession, AuthenticatedKey)
├── main.py         # App factory
├── middleware/     # Error handler
├── models/         # ORM models (DO NOT put business logic here)
├── routers/        # Route handlers (thin transport ONLY)
├── schemas/        # Pydantic request/response models
├── services/       # Business logic (ALL domain logic goes here)
└── utils/          # Shared utilities
```
