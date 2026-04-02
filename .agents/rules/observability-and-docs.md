---
trigger: always_on
description: Logging, Documentation, & README Currency
---

## 1. Python Logging Standards
* **Rule:** Use the `logging` module with explicit level values for structured observability. Never leave bare `print()` statements.
* **Enforcement:**
  * `logging.ERROR` — Exceptions, callout failures, database errors.
  * `logging.WARNING` — Unexpected but recoverable conditions (e.g., cache miss, Redis unavailable).
  * `logging.INFO` — Key execution milestones (e.g., "Briefing generated for account: {name}", "Agent Engine call completed in {ms}ms").
  * `logging.DEBUG` — Detailed diagnostic data (e.g., full request/response payloads). Remove or guard these before merging to `main`.
* **Format:** All log messages must use structured formatting: `logger.info("Briefing generated", extra={"account_id": id, "latency_ms": ms})`.

## 2. Docstring Headers
* **Rule:** Every public class and function MUST have a docstring.
* **Enforcement:** Use Google-style docstrings:
  ```python
  def generate_briefing(request: BriefingGenerateRequest) -> BriefingResponse:
      """Generate an AI strategic briefing for the given entity.

      Args:
          request: Validated briefing request with account/contact context.

      Returns:
          BriefingResponse with cached or freshly generated briefing.

      Raises:
          HTTPException: If the entity type is unsupported or auth fails.
      """
  ```

## 3. README Currency Mandate
* **Rule:** Any time a new endpoint, environment variable, Docker service, deployment prerequisite, or database migration is introduced, the `README.md` must be updated in the same commit.
* **Enforcement:** The README must always maintain the sections defined in `project-governance.md` Rule 3.

## 4. No Silent Failures
* **Rule:** Every `try/except` block must explicitly log the error before re-raising or returning.
* **Enforcement:** Catch blocks must call `logger.error(...)` with the exception message and traceback, then raise an `HTTPException` with a sanitized, user-friendly message. Never swallow exceptions silently. Never expose raw stack traces to API clients.

## 5. AI Usage Logging
* **Rule:** Every call to the Vertex AI Agent Engine or raw Gemini model MUST log an entry to the `ai_usage_logs` table.
* **Enforcement:** Log entries must capture: endpoint, operation, user_identifier, entity_type, entity_id, tokens_used, input_tokens, output_tokens, latency_ms, cache_hit, status, error_message, and model_name. Logging must be non-blocking — use `asyncio.create_task()` or background tasks so logging failures never block the API response.
