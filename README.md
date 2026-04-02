# Gemini Sales Accelerator Core

A headless AI Enterprise Platform that generates AI-powered Strategic Sales Briefings via REST API. Multi-tenant by design — any CRM, spreadsheet, or custom frontend can call the same API to get AI-generated strategic intelligence, P2B scoring, and deal coach analysis powered by Vertex AI.

## Table of Contents

- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [API Endpoint Reference](#api-endpoint-reference)
- [Security Patterns](#security-patterns)
- [Data Model](#data-model)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Directory Structure](#directory-structure)
- [Contributing](#contributing)
- [License](#license)

## Key Features

| Feature | Description | Status |
|---|---|---|
| **AI Strategic Briefings** | Strategic summary, discovery questions, anticipated objections, and a recommended opening — generated per Account, Contact, or Opportunity | ✅ Implemented |
| **P2B Scoring & Account Signal** | AI-generated Propensity to Buy score (0–100) with a contextual Account Signal | ✅ Schema Ready |
| **Multi-Tenant Campaign Context** | Dynamic `campaign_context` field personalizes "Why We Matter" and objection handling per client team's product focus | ✅ Implemented |
| **Inline Data Upsert** | CRM data passed inline per-request — upserted idempotently via `(source_system, external_id)` natural key | ✅ Implemented |
| **TTL-Based Briefing Cache** | Configurable cache expiration prevents redundant AI calls. Force-refresh available on demand | ✅ Implemented |
| **Buying Committee Suggestions** | AI-suggested buyer personas with titles and relevance reasons | ✅ Schema Ready |
| **Deal Coach Analysis** | "Why We Matter", anticipated objection, and strategic pivot — all personalized to the contact's role | ✅ Schema Ready |
| **Multi-Source Identity** | Accounts from Salesforce, Google Sheets, HubSpot, or custom systems are deduplicated by `(source_system, external_id)` | ✅ Implemented |
| **AI Usage Logging** | Token usage, latency, cache hit rate, and error tracking for every agent call | ✅ Schema Ready |
| **Google Sheets Client** | TTEC Digital branded sidebar — highlight a row, generate a briefing, never leave the spreadsheet | ✅ Implemented |

---

## Architecture

```
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│   Presentation Layer │      │    Core API Layer     │      │  Intelligence Layer  │
│   (Tier 1 — Clients) │─────▶│  (Tier 2 — FastAPI)  │─────▶│ (Tier 3 — Vertex AI) │
│                      │ HTTP │                      │  SDK │                      │
│ • Google Sheets      │      │ • REST API (/api/v1) │      │ • Briefing Agent     │
│ • Salesforce (future)│      │ • PostgreSQL 15      │      │ • Chat Agent         │
│ • Custom Web Apps    │      │ • Redis 7            │      │ • (Future Agents)    │
└──────────────────────┘      └──────────────────────┘      └──────────────────────┘
```

**Strict layer isolation** (architecture.md §4): `clients/` ↛ `api/` ↛ `intelligence/`. Cross-tier communication via HTTP only. No direct Python imports across boundaries.

| Layer | Responsibility | Tech Stack |
|---|---|---|
| **Presentation** | User-facing frontends — send data, render results | Google Apps Script, HTML, JavaScript |
| **Core API** | REST endpoints, auth, database, caching, business logic | Python 3.12, FastAPI, SQLAlchemy 2.0, asyncpg, Redis |
| **Intelligence** | AI agent orchestration, Vertex AI integration | Vertex AI Agent Engine, Gemini models |

---

## Prerequisites

- **Docker Desktop** ≥ 4.x (with Docker Compose v2)
- **Python** 3.12+ (for local linting / IDE support — runtime is containerized)
- **Google Cloud SDK** (for Vertex AI agent wiring)
- **Git** ≥ 2.x

---

## Environment Setup

Copy the example env file and configure for your local setup:

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

> [!IMPORTANT]
> Never commit `.env`, `.env.local`, or `.env.prod` to version control. Only `.env.example` is tracked.

---

## Local Development

Start all services with a single command:

```bash
docker compose up
```

This spins up:

| Service | Container | Host Port | Container Port |
|---|---|---|---|
| **PostgreSQL 15** | `gsa-postgres` | `5432` | `5432` |
| **Redis 7** | `gsa-redis` | `6380` | `6379` |
| **FastAPI API** | `gsa-api` | `8000` | `8000` |

Code changes in `api/` are hot-reloaded automatically via volume mount + `uvicorn --reload`.

### Rebuild After Dependency Changes

```bash
docker compose up --build
```

### Tear Down (Including Data)

```bash
docker compose down -v
```

---

## API Endpoint Reference

All authenticated endpoints require the `X-API-Key` header.

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

### Briefing Response Schema

| Field | Type | Description |
|---|---|---|
| `id` | `uuid` | Briefing cache record ID |
| `entity_type` | `string` | `account`, `contact`, or `opportunity` |
| `entity_id` | `uuid` | ID of the briefed entity |
| `briefing_markdown` | `string` | Account-level strategic briefing in Markdown |
| `contact_briefing_markdown` | `string` | Contact-specific executive briefing |
| `p2b_score` | `integer` | Propensity to Buy score (0–100) |
| `account_signal` | `string` | 1–2 sentence strategic signal |
| `why_we_matter` | `string` | Value proposition statement |
| `anticipated_objection` | `string` | Most likely executive objection |
| `objection_pivot` | `string` | Strategic pivot to redirect |
| `suggested_contacts` | `array` | `[{"title": "...", "reason": "..."}]` |
| `generated_at` | `datetime` | When the briefing was generated |
| `expires_at` | `datetime` | When the cache expires |
| `cache_hit` | `boolean` | Whether served from cache |

---

## Security Patterns

| Pattern | Implementation |
|---|---|
| **Authentication** | API key via `X-API-Key` header, validated in `dependencies.py` |
| **Input Validation** | Strict Pydantic `Field()` constraints with min/max length, ge/le |
| **Zero Hardcoding** | All secrets, project IDs, and URLs via `config.py` → env vars |
| **Safe Null Overwrites** | AI-returned `null` never overwrites existing enrichment data |
| **Upsert Idempotency** | `(source_system, external_id)` as natural key — no duplicates |
| **Error Sanitization** | `global_exception_handler` returns user-friendly messages, never stack traces |
| **No .env in VCS** | `.gitignore` blocks `.env`, `.env.local`, `.env.prod` |
| **GCP Auth** | ADC in production, service account key via Docker volume in dev |

---

## Data Model

```mermaid
erDiagram
    Account ||--o{ Contact : has
    Account ||--o{ Opportunity : has
    Account ||--o{ BriefingCache : cached_by
    Contact ||--o{ BriefingCache : cached_by

    Account {
        uuid id PK
        string external_id "Unique per source_system"
        string source_system "salesforce, google_sheets, etc."
        string name "Company name"
        string industry
        float annual_revenue
        int p2b_score "AI: Propensity to Buy (0-100)"
        text account_signal "AI: Strategic signal"
        text suggested_contacts_json "AI: Buying committee JSON"
    }

    Contact {
        uuid id PK
        uuid account_id FK
        string first_name
        string last_name
        string title
        string email
    }

    Opportunity {
        uuid id PK
        uuid account_id FK
        string name
        string stage_name
        float amount
        date close_date
    }

    BriefingCache {
        uuid id PK
        string entity_type "account, contact, opportunity"
        uuid entity_id "Polymorphic FK"
        text briefing_markdown
        text contact_briefing_markdown
        int p2b_score "Snapshot at generation"
        text why_we_matter
        text anticipated_objection
        text objection_pivot
        int cache_ttl_days "Default: 7"
        datetime expires_at
    }

    AIUsageLog {
        uuid id PK
        string endpoint
        string operation
        int tokens_used
        int latency_ms
        boolean cache_hit
        string status
    }

    PlatformConfig {
        uuid id PK
        string key "Unique config key"
        text value "Runtime-changeable value"
    }
```

---

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
docker compose exec postgres psql -U gsa_user -d postgres \
  -c "CREATE DATABASE gsa_core_test OWNER gsa_user;"
```

### Coverage Target

≥85% aggregate coverage across `api/app/` (currently at **86%**).

### Test Matrix

| Test File | Tests | Category |
|---|---|---|
| `test_health.py` | 1 | Health endpoint |
| `test_briefings.py` | 12 | Happy path, cache, upsert, sad path, auth |
| `test_schemas.py` | 12 | Pydantic validation, edge cases, max_length |
| **Total** | **25** | **86% coverage** |

---

## Troubleshooting

### Docker: Port 5432 Already in Use

If you have a local PostgreSQL running, stop it or change the host port in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"  # Map to 5433 instead
```

### Docker: Port 6379 Already in Use (Redis)

Redis is mapped to host port `6380` by default to avoid conflicts with any local Redis instance.

### Tests: `CREATE DATABASE gsa_core_test` Error

If the test database already exists, you can safely ignore the error. To recreate:

```bash
docker compose exec postgres psql -U gsa_user -d postgres \
  -c "DROP DATABASE IF EXISTS gsa_core_test;" \
  -c "CREATE DATABASE gsa_core_test OWNER gsa_user;"
```

### API: 401 Unauthorized

Ensure you're passing the `X-API-Key` header with the value from your `.env` file:

```bash
curl -H "X-API-Key: gsa_dev_key_change_me_in_production" http://localhost:8000/health
```

### API: 500 on Briefing Generate

Check that all Docker services are healthy:

```bash
docker compose ps
```

All three containers (`gsa-postgres`, `gsa-redis`, `gsa-api`) should show `healthy` or `running`.

---

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
│   │   ├── routers/        # FastAPI route handlers (thin transport only)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # Business logic (briefing_service.py)
│   │   └── utils/          # Shared utilities
│   ├── tests/              # pytest test suite (25 tests, 86% coverage)
│   ├── .env.example        # Environment variable template
│   ├── Dockerfile          # Dev container (Python 3.12-slim)
│   ├── pyproject.toml      # Pytest configuration
│   └── requirements.txt    # Pinned Python dependencies
├── clients/
│   └── google-sheets/      # Google Sheets Apps Script client
│       ├── src/            # Server-side GS modules (5 files)
│       ├── views/          # HTML sidebar & settings dialog
│       └── README.md       # Client-specific setup instructions
├── intelligence/           # (Phase 3) Vertex AI agent definitions
│   ├── agents/             # Agent class implementations
│   └── shared/             # Cross-agent utilities
├── docker-compose.yml      # Local development stack (Postgres, Redis, API)
├── CONTRIBUTING.md         # Developer guide, standards, PR process
├── LICENSE                 # Project license
└── README.md               # ← You are here
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, coding standards, testing requirements, and the PR process.

## License

See [LICENSE](LICENSE) for details.
