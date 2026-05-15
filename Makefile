.PHONY: install generate check-generate test test-all run lint clean

# Install runtime + dev dependencies into a local .venv.
install:
	uv sync --all-extras

# Regenerate app/generated/_input.py + manifest.json from contract/app.pkl.
# Requires `pkl` CLI: https://pkl-lang.org/main/current/pkl-cli/index.html
generate:
	pkl eval --project-dir contract -m app/generated contract/app.pkl

# Fail if the checked-in generated files drift from the Pkl source. Used by CI.
check-generate: generate
	@git diff --exit-code app/generated/ \
		|| (echo "ERROR: app/generated/ is stale. Run 'make generate' and commit." && exit 1)

# Fast unit tests.
test:
	uv run pytest tests/unit -q

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
