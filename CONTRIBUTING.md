# Contributing

This repo is a teaching reference, not a feature-rich product, so the bar for
new files is "does this make the example *clearer* to a first-time reader?"
Bug fixes, doc improvements, and SDK-version bumps are always welcome.

## Setup

```bash
uv sync --all-extras
uv run pre-commit install
```

## Workflow

1. Branch off `main`.
2. Make your change. Keep the diff small and the README in sync.
3. Run `make lint && make test`.
4. Open a PR. The `checks.yml` workflow re-runs lint + unit tests.

## Releases

The repo is versioned in `pyproject.toml`. There is no release pipeline —
tagging `vX.Y.Z` on `main` is enough for downstream readers to pin a known-
good revision.

## Reporting issues

File a GitHub issue with:

- What you tried (paste the commands or curl invocations).
- What you expected.
- What happened — full error message and the relevant log lines.

For questions about the SDK itself, file in
[atlanhq/application-sdk](https://github.com/atlanhq/application-sdk/issues)
instead.
