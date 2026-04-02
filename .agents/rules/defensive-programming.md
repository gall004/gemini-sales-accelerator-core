---
trigger: always_on
description: Null Safety, Graceful Degradation, & Defensive Patterns
---

## 1. Null Coalescing in All External Data
* **Rule:** When processing data from external sources (API requests, Vertex AI responses, database records, CRM data passed inline), every field reference must use defensive null handling.
* **Enforcement:** Use Python's `or` operator, `dict.get()` with defaults, or explicit `if x is not None` checks. Never access nested dictionary keys without guarding each level.

## 2. Safe AI Response Parsing
* **Rule:** Never assume the Vertex AI Agent Engine response structure is valid. Defensively parse every response.
* **Enforcement:**
  1. Validate HTTP status code before parsing the body.
  2. Use multi-strategy JSON extraction: strip markdown fences → direct parse → brace-matching extraction → raw text fallback.
  3. If JSON parsing fails, return the raw AI text to the user — they see the AI's actual output rather than a generic error message.
  4. Use `safeint()`, `safestr()`, and `safefloat()` helper functions for type-coercing AI-returned values that may be strings instead of numbers.

## 3. Safe Null Overwrites for AI-Returned Data
* **Rule:** When the AI returns `null` for a field that already has a value in the database (e.g., `p2b_score`, `annual_revenue`), do NOT overwrite the existing value with null.
* **Enforcement:** Before updating an enrichment field, check `if ai_value is not None`. This preserves existing data when the AI cannot find entity-specific or recent information.

## 4. Upsert Idempotency
* **Rule:** All upsert operations (account, contact, opportunity) must be idempotent — calling the same endpoint with the same data twice must not create duplicates or corrupt existing records.
* **Enforcement:** Upserts use `(source_system, external_id)` as the natural key. If no `external_id` is provided, a new record is created. If one is provided, the existing record is updated with non-null fields only.

## 5. Graceful External Service Degradation
* **Rule:** If Redis is unavailable, the API must continue operating using PostgreSQL as the fallback cache. If the Vertex AI agent is unavailable, the API must return a clear error without crashing.
* **Enforcement:** Redis operations must be wrapped in `try/except` blocks that log warnings and fall through to the database path. Agent Engine timeouts must return HTTP 503 with a retry-friendly error message.

## 6. Request Timeout Enforcement
* **Rule:** All external HTTP calls (Vertex AI, Google APIs) must have explicit timeouts.
* **Enforcement:** Set `timeout=60` (seconds) on all Vertex AI SDK calls. The FastAPI endpoint itself should never hang longer than 90 seconds. If an agent call exceeds the timeout, log the failure and return a 504 Gateway Timeout.
