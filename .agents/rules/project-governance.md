---
trigger: always_on
description: Project Governance, Meta-Documentation, & Living Standards
---

## 1. The CONTRIBUTING.md Currency Mandate
* **Rule:** If you introduce a new testing pattern, modify the Git branching strategy, add a deployment prerequisite, or change coding standards, you MUST proactively update `CONTRIBUTING.md` in the same commit.
* **Enforcement:** `CONTRIBUTING.md` must always serve as a strictly accurate, single source of truth for a new developer joining the project.

## 2. Licensing & Copyright
* **Rule:** Ensure the root `LICENSE` file remains intact. Do not overwrite or delete it during project scaffolding.
* **Enforcement:** If making widespread project updates and the copyright year is outdated, proactively offer to update it.

## 3. README Currency Mandate
* **Rule:** Any time a new environment variable is introduced, a GCP service is enabled, a Docker service is added, or an architectural decision is made, the `README.md` must be updated in the same commit.
* **Required Structure:** The `README.md` must always maintain:
  1. Project overview and strategic context
  2. Architecture diagram / description
  3. Prerequisites (Docker, GCP project, APIs, service accounts)
  4. Environment setup (`.env` variables)
  5. Local development instructions (`docker compose up`)
  6. API endpoint reference
  7. Testing instructions (`pytest` commands)
  8. Directory structure reference

## 4. Definition of Done Enforcement
* **Rule:** No code is submitted for review until all items in the Pre-Flight Self-Review Checklist (see `git-workflow.md`) are satisfied.
* **Enforcement:** The AI agent must self-verify all checklist items before presenting any Review Summary to the user.

## 5. Documentation Verification Gate
* **Rule:** Before every commit, the AI agent MUST scan the staged diff against the Trigger → Document Matrix defined in `.agents/workflows/sdlc-workflow.md` (Step 5). If any trigger fires, the corresponding document update is mandatory in the same commit.
* **Enforcement:** The agent must output a Documentation Gate checklist (✓/✗ for each trigger) before staging. A commit with an unfulfilled ✗ item is blocked. This applies to ALL commits — SDLC workflow, quick fixes, hotfixes, and ad-hoc changes alike.
