---
trigger: always_on
description: Test-Driven Development, Coverage Requirements, & Quality Assurance
---

## 1. The TDD Mandate
* Before writing the implementation code for a new service, utility, or complex endpoint, you must first write a failing pytest test.
* You must execute the test to confirm it fails (Red).
* You will then write the implementation code to satisfy the test.
* You must execute the test to confirm it passes (Green) before pushing.

## 2. Testing Stack Rules
* **pytest (`api/tests/`):** Use for all API endpoint tests, service layer tests, and utility function tests. Use `httpx.AsyncClient` with `app.dependency_overrides` for endpoint tests.
* **pytest-asyncio:** Use for all async test functions. Mark with `@pytest.mark.asyncio`.
* **conftest.py:** Shared fixtures (test database, test client, mock Vertex AI responses) live in `api/tests/conftest.py`. Each test module may have its own `conftest.py` for module-specific fixtures.

## 3. Code Coverage Mandate
* **Rule:** The project must maintain ≥85% aggregate code coverage across the `api/app/` directory.
* **Enforcement:** Run `pytest --cov=app --cov-report=term-missing` to verify. Any new service or router module must ship with corresponding test coverage.

## 4. Sad-Path Test Enforcement
* **Rule:** TDD is not just for the "Happy Path". You must explicitly write tests that prove your code handles failure gracefully.
* **Enforcement:** For every service method or endpoint, you must write at least:
  * One test for invalid input (e.g., missing required fields, invalid entity_type).
  * One test for external service failure (e.g., Vertex AI timeout, database connection error).
  * One test for authentication failure (missing or invalid API key).
  * One test verifying the error response structure matches the expected JSON format.

## 5. Mock External Services
* **Rule:** Tests must NEVER make real HTTP callouts to Vertex AI, Google APIs, or any external service.
* **Enforcement:** Use `unittest.mock.patch` or `pytest-mock` to mock the Vertex AI SDK client. Create a dedicated `api/tests/mocks/` directory for reusable mock response factories that return realistic JSON responses matching the Agent Engine output schema.

## 6. Database Test Isolation
* **Rule:** Each test must run against an isolated database state. Tests must not depend on data created by other tests.
* **Enforcement:** Use a test database (separate from development) with transaction rollback per test. The `conftest.py` fixture must create a fresh async session per test and roll back after each test completes.

## 7. The Human-in-the-Loop Handover
* When presenting a completed feature to the user, you must include the test output or coverage summary in your handover message to prove the code is stable.
