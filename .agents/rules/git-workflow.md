---
trigger: always_on
description: Safe Git Workflow for Monorepo Development
---

## 1. The Branch Check Mandate
* Before you write, modify, or delete any code files, you must determine the current Git branch by running: `git branch --show-current`.
* If the current branch is `main` or `master`, YOU MUST NOT make any file changes yet.

## 2. Automatic Branch Creation
* **Main Branch:** If the user requests a feature, refactor, or bug fix while on the `main` or `master` branch, you must proactively generate a contextual branch name (e.g., `feat/briefing-service`, `fix/cache-ttl`) and run `git checkout -b <branch-name>`.
* **Other Branches:** If already on a non-main feature branch:
  * If the user's request is related to the current work, keep going on the same branch.
  * If the request is unrelated, prompt the user asking if they want a new branch.

## 3. Conventional Commits
* **Rule:** Every commit message MUST follow the Conventional Commits specification: `feat:`, `fix:`, `chore:`, `refactor:`, `test:`, `docs:`.
* **Enforcement:** Include a concise scope when applicable (e.g., `feat(api): add briefing service`, `fix(intelligence): handle empty agent response`). Commit messages must be descriptive enough that `git log --oneline` serves as a readable project changelog.
* **Monorepo Scopes:** Use these standard scopes:
  * `api` — Core API & database changes
  * `intelligence` — Vertex AI agent changes
  * `sheets` — Google Sheets client changes
  * `infra` — Docker, CI/CD, deployment changes
  * `docs` — Documentation-only changes

## 4. The Pre-Flight Self-Review Checklist
* Before you stage, commit, and present your work, you MUST independently verify:
  1. **No Debug Leftovers:** You have removed all temporary `print()` statements and bare `logger.debug()` calls used during development.
  2. **No Hardcoded Secrets:** You have not hardcoded any API keys, GCP project IDs, database passwords, or service account emails anywhere in the codebase.
  3. **No Commented-Out Code:** Blocks of commented-out code have been removed. Use version control to preserve history, not comments.
  4. **No `.env` Files:** You have not staged `.env`, `.env.local`, or `.env.prod` — only `.env.example` is committed.

## 5. Human-in-the-Loop Code Review & Handoff
* **The Hard Stop:** When you have completed a feature on a feature branch and passed the Pre-Flight Checklist, YOU MUST NOT merge the branch into `main` automatically.
* **The Commit & Push:**
  1. Stage all changes with `git add .`.
  2. Commit with a descriptive conventional commit message.
  3. Push the feature branch to the remote repository.
* **The Handoff:** After pushing, STOP and present a "Review Summary" to the user.
* **NO AUTOMATED PRs:** You MUST NOT run `gh pr create` or `gh pr merge` automatically after pushing. Wait for the user to explicitly grant permission to open and/or merge the Pull Request.

## 6. No Direct Pushes to Main
* **CRITICAL RULE:** You are NEVER permitted to push commits directly to the `main` or `master` branch.
* **Pull Requests Only:** All code integrations into `main` MUST occur via Pull Requests. Even if the user explicitly says "merge this to main", you must first ask for permission to use the GitHub CLI to open a PR.
