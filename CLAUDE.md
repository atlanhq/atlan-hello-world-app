# CLAUDE.md — Atlan AI Agent Quick Reference (Claude Code Edition)

> **Version:** 6.1 | **Updated:** 2026-03-26  
> **Full Policy:** See `AGENTS.md` for all domain-specific rules and checklists.  
> **Security Contact:** Slack `#bu-security-and-it`

---

## Project Overview

Reference "hello world" app for the Atlan Application SDK. Two `@task`s, one
workflow, no external system, no credentials. Designed so an external
developer can read it top-to-bottom in 15 minutes and copy it as a template
for a real connector.

Keep that audience in mind for every change: clarity beats cleverness.

## Project Commands

- Install: `uv sync --all-extras`
- Run dev server: `make run` (needs Temporal: `temporal server start-dev`)
- Unit tests: `make test`
- Lint + format + type-check: `make lint`
- Regenerate contracts from Pkl: `make generate`
- Verify generated files are not stale: `make check-generate`

## Coding Conventions

- Python 3.11+. Style: ruff (lint + format), pyright in standard mode.
- Logging: `self.logger` from `App`. Use `%s` formatting (not f-strings) so
  log records stay queryable.
- Errors: raise typed errors from `application_sdk.errors`
  (`InvalidInputError`, `DependencyUnavailableError`, `InternalError`).
  Never raise bare `Exception` or `ValueError` from task code.
- Contracts: every `@task` takes one `Input` subclass and returns one
  `Output` subclass. Adding a field is fine; renaming or removing one is a
  breaking change.
- The top-level workflow input is generated from `contract/app.pkl`. Do not
  hand-edit `app/generated/`; edit the Pkl source and run `make generate`.

## Architecture Notes

- `App.run()` is the Temporal workflow function — it must be deterministic.
  Anything that touches the outside world (network, disk, clock) goes inside
  a `@task`-decorated method.
- Pkl drives both the Atlan UI form and the Python typed input — single
  source of truth for the workflow schema.
- This repo is a teaching artifact, not a production connector. Reject
  changes that add domain complexity (credentials, asset mapping,
  publish-app handoff) which obscure the minimum viable shape — push those
  into a real connector repo instead.
- All CI must be runnable on an external fork. Workflows depending on
  Atlan-internal secrets or actions should be omitted or guarded.

---

## Security Quick Reference

### Tags

`[MUST]` = required | `[REDLINE]` = forbidden | `[SHOULD]` = best practice

### Always-Check Invariants (Every Change)

1. **[MUST] No secrets** in code, config, logs, CI output, or `.env` files in version control.
2. **[MUST] Auth & authz must be real** — every protected endpoint must verify identity (JWT, OAuth, API key, session, OIDC, etc.) and enforce permissions. No phantom middleware.
3. **[MUST] No wildcards** — no `CORS: *`, `Action:"*"`, RBAC `resources:["*"]`, or `write-all`.
4. **[MUST] No untrusted execution** — no `eval`, unsafe deserialization, command injection, or CI `run:` injection.
5. **[MUST] Pin supply chain** — actions→SHA, images→version/SHA, no `latest`, verify deps exist.

### Conditional Checks (When Relevant)

| When you see... | Check |
|-----------------|-------|
| DB queries | **[MUST]** Parameterized only; tenant/org scoping if multi-tenant |
| New API endpoint | **[MUST]** Auth, authz, input validation, rate limiting — all before merge |
| Auth/session code | **[MUST]** Validate credentials properly (JWT, API key, OAuth, session — whatever the service uses). Tokens must expire. **[SHOULD]** Use established auth libraries. |
| Error responses | **[MUST]** Generic to clients; no internals leaked |
| Outbound HTTP with user input | **[MUST]** Allowlist hosts; block internal/metadata IPs |
| Logging | **[REDLINE]** Never log tokens, cookies, secrets, Authorization headers |
| Dependencies | **[MUST]** Block CRITICAL/HIGH CVEs; check typosquatting |
| CI/CD workflows | **[MUST]** Pin actions to SHA; minimum permissions; no injection |
| Helm/K8s | **[MUST]** Non-root, read-only FS, drop all caps; least-privilege RBAC |
| Frontend | **[REDLINE]** No `dangerouslySetInnerHTML`/`v-html`/`innerHTML` with user data. **[MUST]** No tokens in localStorage/sessionStorage. Validate redirects. CSRF if cookie auth. Sanitize rich text (DOMPurify). **[SHOULD]** Strict CSP; no source maps in prod; no PII in client state/URLs. |
| AI/LLM | **[MUST]** No raw user input in system prompts. Mask PII/secrets before LLM calls. Sanitize output before UI rendering. No LLM output for auth decisions. No customer data to external LLMs without approval. **[REDLINE]** LLM output to `eval`, SQL, shell, or `innerHTML`. **[SHOULD]** Rate limit LLM API calls. |

> For full details on each domain, see `AGENTS.md § Conditional Checks`.

### Severity & Response

| Severity | Action |
|----------|--------|
| **CRITICAL** | **Block.** Fix immediately. No opt-out. |
| **HIGH** | **Block.** Fix before merge. No opt-out. |
| **MEDIUM** | Flag with recommended fix. Can be follow-up. |
| **LOW** | Note briefly. |

### Review Output (MEDIUM+)

```txt
🔒 SECURITY REVIEW
Issue: [description]
Severity: CRITICAL | HIGH | MEDIUM
Location: [file:line]
Risk: [what attacker gains]
Fix: [concrete fix — implement immediately for CRITICAL/HIGH]
```

### Existing Violations

- **In your diff:** Fix or flag with 🔒 format.
- **Outside your diff:** Note briefly. Don't refactor without approval.
- **Never** use existing violations to justify new ones.

### Manual Security Review

Reach out to `#bu-security-and-it` before merging when changes touch auth/authz, multi-tenant isolation, secrets management, new public endpoints, or anything you're unsure about.