# CLAUDE.md

This file provides guidance for AI assistants (Claude and others) working in this repository.

## Repository Overview

**Repository:** `Mhnggs/fxtestproto`
**Status:** Initial setup — no source code has been committed yet.

> This CLAUDE.md was generated at repository initialization. Update all sections below as the project evolves.

---

## Project Purpose

_To be filled in once the project scope is defined. Describe what this repository does, who uses it, and what problem it solves._

---

## Repository Structure

_No source files exist yet. Update this section when the project structure is established._

Expected layout (update as needed once files are added):

```
fxtestproto/
├── CLAUDE.md          # This file
├── README.md          # Human-facing documentation (create when ready)
└── .git/              # Git metadata
```

---

## Development Setup

### Prerequisites

_List required tools, runtimes, and versions here once the stack is chosen._

### Getting Started

```bash
# Clone the repository
git clone <repo-url>
cd fxtestproto

# Install dependencies (update command for your stack)
# e.g.: npm install | pip install -r requirements.txt | go mod download

# Run the project (update command for your stack)
# e.g.: npm run dev | python main.py | go run .
```

---

## Build & Run

_Update these commands once the build system is established._

```bash
# Build
# e.g.: npm run build | make build | go build ./...

# Run
# e.g.: npm start | ./bin/app | go run .
```

---

## Testing

_Update these commands once the test suite is established._

```bash
# Run all tests
# e.g.: npm test | pytest | go test ./...

# Run tests with coverage
# e.g.: npm run test:coverage | pytest --cov | go test -cover ./...
```

### Testing Conventions

- Write tests alongside source files or in a dedicated `tests/` or `*_test.*` directory (per language convention).
- Tests should be deterministic and not rely on external services unless mocked.
- Aim for meaningful coverage of business logic, not just line coverage.

---

## Code Style & Conventions

_Update these rules to match the linting/formatting tools chosen for this project._

### General

- Prefer clarity over cleverness.
- Keep functions small and focused on a single responsibility.
- Avoid over-engineering: only add abstractions when they are clearly needed.
- Do not add error handling for scenarios that cannot happen.

### Naming

- Use descriptive, intention-revealing names.
- Follow the naming conventions of the chosen language (e.g., `camelCase` for JS/TS, `snake_case` for Python, etc.).

### Comments

- Only add comments where the logic is not self-evident.
- Do not add docstrings or type annotations to code you did not write or change.

### Formatting

_Update once a formatter is configured (e.g., Prettier, Black, gofmt)._

```bash
# Format code
# e.g.: npm run format | black . | gofmt -w .
```

---

## Git Workflow

### Branch Naming

- Feature branches: `feature/<short-description>`
- Bug fix branches: `fix/<short-description>`
- Claude/AI branches: `claude/<description>-<session-id>`

### Commit Messages

- Use the imperative mood: "Add feature" not "Added feature".
- Keep the subject line under 72 characters.
- Reference issue numbers when applicable: `Fix login bug (#42)`.

### Pull Requests

- All changes should go through a pull request.
- Include a clear description of what changed and why.
- Ensure tests pass before requesting review.

---

## Environment Variables

_List required environment variables here once they are known._

```bash
# Example:
# APP_ENV=development
# DATABASE_URL=...
# API_KEY=...
```

Do **not** commit `.env` files or secrets to the repository.

---

## Key Conventions for AI Assistants

1. **Read before editing.** Always read a file before modifying it.
2. **Minimal changes.** Only change what is directly requested. Do not refactor unrelated code.
3. **No speculative features.** Do not add functionality that was not asked for.
4. **Prefer editing over creating.** Modify existing files rather than creating new ones when possible.
5. **Security first.** Never introduce SQL injection, XSS, command injection, or other OWASP Top 10 vulnerabilities.
6. **No secrets in code.** Never hardcode credentials, API keys, or tokens.
7. **Match existing style.** Follow the code style already present in the file being edited.
8. **Check tests.** After making changes, verify that the test suite still passes.
9. **Commit on the correct branch.** Always develop on the branch specified in task instructions (`claude/...` branches for AI tasks).
10. **Push only when asked.** Do not push to remote unless explicitly instructed.

---

## CI/CD

_Update this section once a CI/CD pipeline is configured._

No CI/CD pipeline has been set up yet. When added, document:
- Which checks run on PRs (lint, test, build)
- Deployment targets and how deployments are triggered
- Any required secrets that must be configured in the repository settings

---

## Updating This File

Keep this file current as the project grows:
- Add new tools, commands, or conventions as they are introduced.
- Remove placeholder sections once real content replaces them.
- Record any non-obvious architectural decisions with a brief rationale.
