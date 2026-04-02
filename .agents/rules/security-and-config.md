---
trigger: always_on
description: Zero-Hardcoding, Secrets Management, & Environment Configuration
---

## 1. Zero Hardcoding Policy (Secrets & Config)
* **Rule:** Never hardcode secrets, credentials, OR environment-specific configurations (like GCP project IDs, model names, API endpoints, agent engine IDs, or database URLs).
* **Enforcement:** Always extract these values using `Settings` fields in `api/app/config.py` (which reads from `os.environ` via Pydantic Settings) or the `platform_config` database table for runtime-changeable values.

## 2. Environment Parity & The `.env` Lifecycle
* **The Currency Mandate:** Any time a new environment variable is introduced into the codebase, you MUST simultaneously:
  1. Add it to `api/.env.example` with a descriptive dummy value or instructional comment.
  2. Add the corresponding field to `api/app/config.py` (`Settings` class) with type validation.
  3. Add it to the `docker-compose.yml` environment section for the relevant service.
  4. Explicitly inform the user in your handover message that they must add the new key to their local `.env` file.
  5. Update the `README.md` Environment Variables section.
* **Never commit `.env`, `.env.local`, or `.env.prod` to version control.**

## 3. Docker Compose as Source of Truth
* **Rule:** For local development, `docker-compose.yml` is the single source of truth for all service credentials and configuration.
* **Enforcement:** The API container's environment block must mirror `.env.example`. If you add a variable to one, you MUST add it to both. Database credentials, Redis URLs, and GCP project IDs are set in docker-compose and injected into the container — never read from a file inside the container.

## 4. Google Cloud IAM — No Service Account Keys in Code
* **Rule:** The Intelligence Layer and Core API authenticate to GCP using Application Default Credentials (ADC) in production and service account key files mounted as Docker volumes in development. Keys are NEVER committed to the repository.
* **Enforcement:** If a GCP credential file is needed locally, it must be:
  1. Listed in `.gitignore`
  2. Mounted as a Docker volume in `docker-compose.yml`
  3. Referenced via the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## 5. API Key Security
* **Rule:** The MVP uses API key authentication (`X-API-Key` header). Keys must never appear in client-side code, URL parameters, or git history.
* **Enforcement:** API keys are passed via environment variables and validated in `api/app/dependencies.py`. When multiple keys are needed (per-client), they will be stored in the `platform_config` table — never hardcoded in middleware.
