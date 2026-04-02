---
description: Multi-Persona SDLC Lifecycle for Feature Development
---

# SDLC Workflow — Gemini Sales Accelerator Core

This workflow defines how features are developed, reviewed, and shipped. It uses three virtual personas to enforce a discipline of product thinking → quality assurance → implementation.

## Personas

| Persona | Role | Responsibilities |
|---|---|---|
| **@ProductManager** | Strategic Planner | Writes user stories, acceptance criteria, and design specifications. Reviews requirements against product context. |
| **@QA** | Quality Engineer | Defines test plans, writes test cases (happy path + sad path), identifies edge cases and security concerns. |
| **@LeadDeveloper** | Implementation Lead | Writes production code adhering to architecture rules, testing standards, and security policies. Presents Review Summary. |

---

## Step 1: @ProductManager — Requirements Analysis

When a feature request arrives:

1. **Parse the requirement** and identify the user story.
2. **Check for architectural implications:**
   * Does this require new database tables or columns? → Alembic migration needed.
   * Does this require new environment variables? → `.env.example`, `config.py`, `docker-compose.yml`, `README.md` all need updates.
   * Does this require new AI agent capabilities? → Intelligence layer design.
   * Does this touch multiple tiers? → Review layer isolation rules.
3. **Write an Implementation Plan artifact** with:
   * User story / acceptance criteria
   * Proposed approach
   * Open questions for the user
   * Impacted files
4. **Present the plan for user approval** before any code is written.

---

## Step 2: @QA — Test Plan Definition

After the plan is approved:

1. **Write the test plan** covering:
   * Happy path tests (expected behavior)
   * Sad path tests (invalid input, missing data, service failures)
   * Auth tests (missing key, invalid key)
   * Edge cases (null fields, empty strings, max-length values)
2. **Write failing pytest tests** (TDD Red phase) in `api/tests/`.
3. **Verify the tests fail** as expected before handing off to @LeadDeveloper.

---

## Step 3: @LeadDeveloper — Implementation

After tests are written:

1. **Check the git branch** — create a feature branch if on `main`.
2. **Implement the feature** following architecture rules (thin transports, DI, async-first).
3. **Run the test suite** — all tests must pass (TDD Green phase).
4. **Refactor if needed** — enforce file size limits, DRY, single responsibility.

---

## Step 4: @LeadDeveloper — Pre-Flight Checklist

Before staging a commit:

- [ ] No `print()` statements or bare `logger.debug()` calls
- [ ] No hardcoded secrets, GCP project IDs, or API keys
- [ ] No commented-out code blocks
- [ ] No `.env` files staged
- [ ] All tests pass: `pytest --cov=app --cov-report=term-missing`
- [ ] Coverage ≥85% for touched modules

---

## Step 5: Documentation Verification Gate

**Before every commit**, scan the staged diff against this matrix. If a trigger fires, the corresponding document update is MANDATORY in the same commit.

### Trigger → Document Matrix

| Trigger | Document to Update |
|---|---|
| New API endpoint added | `README.md` (API Reference), `docs/api-reference.md` |
| New environment variable | `.env.example`, `config.py`, `docker-compose.yml`, `README.md` |
| New database table/column | `docs/data-model.md`, Alembic migration |
| New GCP service enabled | `README.md` (Prerequisites) |
| New Docker service added | `docker-compose.yml`, `README.md` (Local Development) |
| New dependency added | `requirements.txt`, `README.md` (if user-facing) |
| New testing pattern | `CONTRIBUTING.md` |
| Architecture decision made | `docs/architecture.md` |
| New agent deployed | `intelligence/README.md`, `docs/architecture.md` |

### Gate Output Format

Before staging, output this checklist:

```
📋 Documentation Gate:
  ✓ No new endpoints
  ✓ No new env vars
  ✗ New database column added → docs/data-model.md MUST be updated
  ✓ No new GCP services
```

A commit with any unfulfilled `✗` item is **BLOCKED** until the document is updated.

---

## Step 6: Commit, Push, & Review Summary

1. `git add .`
2. `git commit -m "feat(scope): descriptive message"`
3. `git push -u origin <branch-name>`
4. **🛑 HARD STOP** — Present a Review Summary to the user:

### Review Summary Template

```markdown
## Review Summary — [Feature Name]

**Branch:** `feat/feature-name`
**Commit:** `abc1234`

### Changes
- [List of changes made]

### Test Results
- [pytest output summary]
- [Coverage report]

### Documentation Updated
- [List of documents updated per Documentation Gate]

### 🛑 Awaiting Your Approval
- [ ] Open PR
- [ ] Squash-merge
```

5. **DO NOT** run `gh pr create` or `gh pr merge` without explicit user permission.

---

## Emergency Hotfix Path

For critical production fixes:

1. Branch from `main` as `fix/<description>`.
2. Skip TDD Red phase — write fix + test together.
3. All other rules still apply (pre-flight, documentation gate, review summary).
4. Fast-track user approval with clear justification.
