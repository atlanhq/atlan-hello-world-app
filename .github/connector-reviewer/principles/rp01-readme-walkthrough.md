---
id: RP01
---
# The README walkthrough still works on the code a developer clones

Principle: This repo is a starter template that external developers clone and follow step by
step. What the README tells them to run or copy (the two run commands, the start and result
requests and their response shape, the two-task model, `make generate`, and the "Make it your own"
list of files that carry the app's name) matches the code in the same commit.
Why: A reader who follows a stale step gets an error or a half-renamed copy on day one, and the
template exists only to make that first run work.
Ask:
- Does the diff change a run command, an endpoint, a request or response field, a task, or a file the README names, without updating the README in the same PR?
- Does the diff add a file or value that carries the hello-world name or id, which a copier must replace but the rename list does not mention?
Don't flag: README drift that predates the diff; the layout tree's `.github/` listing; content the
bootstrap resync manages (the marked block in `CLAUDE.md`, resynced workflows and scripts);
dependency and lock bumps; `CHANGELOG.md`; wording taste. Conformance reports app-name drift
between code, `atlan.yaml` and `.env.example` (`P025`) and unresolved placeholders (`K009`, `O005`).
Severity: High when a documented command or request no longer works as written. Medium for a
missing rename entry or a stale description of the model.
