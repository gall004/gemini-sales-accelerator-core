# Gemini Sales Accelerator Core

Headless AI Enterprise Platform — a multi-tenant REST API that generates AI-powered sales briefings for any TTEC Digital client team.

Owned by **TTEC Digital**. Google Knowledge & Intelligence is the first tenant.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  Presentation Layer  │     │     Core API Layer    │     │  Intelligence Layer  │
│  (Tier 1 — Clients)  │────▶│  (Tier 2 — FastAPI)   │────▶│  (Tier 3 — Vertex AI)│
│                      │HTTP │                       │ SDK │                      │
│ • Google Sheets      │     │ • REST API            │     │ • Briefing Agent     │
│ • Salesforce         │     │ • PostgreSQL + Redis   │     │ • Chat Agent         │
│ • Custom Web Apps    │     │ • Pydantic Validation  │     │ • (Future Agents)    │
└─────────────────────┘     └──────────────────────┘     └──────────────────────┘
```

**Strict layer isolation:** `clients/` ↛ `api/` ↛ `intelligence/`. Cross-tier communication via HTTP only.

## Prerequisites

- **Docker Desktop** ≥ 4.x (with Docker Compose v2)
- **Python** 3.12+ (for local linting / IDE support only — runtime is containerized)
- **Google Cloud SDK** (for eventual Vertex AI agent wiring)
- **Git** ≥ 2.x

## Environment Setup

Copy the example env file and edit for your local setup:

```bash
cp api/.env.example api/.env
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://gsa_user:gsa_local_password@postgres:5432/gsa_core` |
| `DATABASE_URL_SYNC` | Sync PostgreSQL string (Alembic only) | `postgresql://gsa_user:gsa_local_password@postgres:5432/gsa_core` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `API_KEY` | API key for `X-API-Key` header authentication | `gsa_dev_key_change_me_in_production` |
| `APP_ENV` | Environment name (`development`, `test`, `production`) | `development` |
| `GCP_PROJECT_ID` | Google Cloud project ID | `your-gcp-project-id` |
| `GCP_LOCATION` | GCP region for Vertex AI | `us-central1` |
| `LOG_LEVEL` | Python logging level | `INFO` |

## Local Development

Start all services with a single command:

```bash
docker compose up
```

This spins up:
- **PostgreSQL 15** on port `5432`
- **Redis 7** on port `6380` (host) → `6379` (container)
- **FastAPI API** on port `8000` with `uvicorn --reload`

Code changes in `api/` are hot-reloaded automatically via volume mount.

### Rebuild After Dependency Changes

```bash
docker compose up --build
```

### Tear Down (Including Data)

```bash
docker compose down -v
```

## API Endpoint Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | ❌ | Health check — returns `{"status": "ok"}` |
| `GET` | `/docs` | ❌ | Interactive Swagger UI |
| `GET` | `/redoc` | ❌ | ReDoc API documentation |
| `POST` | `/api/v1/briefings/generate` | ✅ `X-API-Key` | Generate an AI strategic briefing |

### Example: Generate Briefing

```bash
curl -X POST http://localhost:8000/api/v1/briefings/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: gsa_dev_key_change_me_in_production" \
  -d '{
    "entity_type": "account",
    "account": {
      "name": "Ticketmaster",
      "industry": "Entertainment",
      "website": "https://ticketmaster.com"
    },
    "contact": {
      "first_name": "Amy",
      "last_name": "Howe",
      "title": "President & CEO"
    },
    "campaign_context": "Google Actions Center Integrations for Event Ticketing",
    "source_system": "google_sheets",
    "external_id": "row_5"
  }'
```

## Testing

Tests run inside the Docker container using `pytest`:

```bash
# Run all tests with coverage
docker compose exec api pytest tests/ --cov=app --cov-report=term-missing -v

# Run a specific test file
docker compose exec api pytest tests/test_briefings.py -v

# Run schema tests only (no DB required)
docker compose exec api pytest tests/test_schemas.py -v
```

### Test Database

Tests use a separate `gsa_core_test` database. Create it once:

```bash
docker compose exec postgres psql -U gsa_user -d postgres -c "CREATE DATABASE gsa_core_test OWNER gsa_user;"
```

### Coverage Target

≥85% aggregate coverage across `api/app/` (currently at 86%).

## Directory Structure

```
gemini-sales-accelerator-core/
├── .agents/
│   ├── rules/              # Governance rules (architecture, testing, security, etc.)
│   └── workflows/          # SDLC workflow definitions
├── api/
│   ├── app/
│   │   ├── config.py       # Pydantic Settings (centralized config)
│   │   ├── database.py     # Async SQLAlchemy engine & session factory
│   │   ├── dependencies.py # FastAPI DI providers (DB, auth, settings)
│   │   ├── main.py         # App factory, lifespan, CORS, router registration
│   │   ├── middleware/     # Error handlers, rate limiting
│   │   ├── models/         # SQLAlchemy ORM models (6 tables)
│   │   ├── routers/        # FastAPI route handlers (thin transport)
│   │   ├── schemas/        # Pydantic request/response models
│   │   └── services/       # Business logic (briefing_service.py)
│   ├── migrations/         # Alembic database migrations
│   ├── tests/              # pytest test suite
│   ├── .env.example        # Environment variable template
│   ├── Dockerfile          # Dev container (Python 3.12-slim)
│   └── requirements.txt    # Pinned Python dependencies
├── clients/
│   └── google-sheets/      # Google Sheets Apps Script client
│       ├── src/            # Server-side GS modules
│       ├── views/          # HTML sidebar & dialog UIs
│       └── README.md       # Client-specific setup instructions
├── intelligence/           # (Phase 3) Vertex AI agent definitions
├── docker-compose.yml      # Local development stack
└── README.md               # ← You are here
```

## Database Schema

6 tables managed by SQLAlchemy ORM + Alembic:

| Table | Purpose |
|---|---|
| `accounts` | Company records with AI enrichment fields (P2B score, signal) |
| `contacts` | Contact records linked to accounts |
| `opportunities` | Opportunity records linked to accounts |
| `briefing_cache` | AI-generated briefing cache with TTL expiration |
| `ai_usage_logs` | Token usage tracking for all AI operations |
| `platform_config` | Runtime-configurable key-value settings |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
