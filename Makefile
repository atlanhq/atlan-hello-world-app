.PHONY: install generate check-generate test test-integration test-all run lint clean

# Install runtime + dev dependencies into a local .venv.
install:
	uv sync --all-extras

# Regenerate atlan.yaml, app.yaml, and app/generated/ from contract/app.pkl.
# Requires `pkl` CLI: https://pkl-lang.org/main/current/pkl-cli/index.html
generate:
	pkl eval --project-dir contract -m . contract/app.pkl

# Fail if the checked-in generated files drift from the Pkl source.
#
# The ruff pass is not optional. `pkl eval` emits generated Python unformatted,
# but the files are committed after pre-commit's ruff hooks have run over them —
# so a raw generate-then-diff reports a file as stale purely because ruff would
# reorder its imports, which it did for app/generated/_e2e_substitutions.py.
# The SDK's generated-freshness workflow formats before diffing for exactly this
# reason; this target has to do the same or it disagrees with the gate it mirrors.
# Version pinned to match .pre-commit-config.yaml — a different ruff formats
# differently, which would reintroduce the same false positive from the other side.
check-generate: generate
	@uvx ruff@0.11.2 check --fix --quiet app/generated/ >/dev/null 2>&1 || true
	@uvx ruff@0.11.2 format --quiet app/generated/ >/dev/null 2>&1 || true
	@git diff --exit-code atlan.yaml app.yaml app/generated/ \
		|| (echo "ERROR: generated files are stale. Run 'make generate' and commit." && exit 1)

# Fast unit tests.
test:
	uv run pytest tests/unit -q

# Integration tier: runs the App on the SDK integration fixture kit (embedded
# Temporal dev server, mocked stores, real in-process worker). No external
# services and no credentials — slower than `test`, still hermetic.
test-integration:
	uv run pytest tests/integration -q

# All tests, including SDR (requires SDR container; see README §SDR tests).
test-all:
	uv run pytest tests -q

# Run the local dev server. Boots the workflow runtime in-process —
# no external services required.
run:
	uv run python -m app.run_dev

# Lint + format (ruff) and type-check (pyright).
lint:
	uv run pre-commit run --all-files

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
