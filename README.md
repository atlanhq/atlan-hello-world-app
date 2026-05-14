# atlan-hello-world-app

The smallest, end-to-end Atlan app — built on the [Application SDK](https://github.com/atlanhq/application-sdk) — designed as the **first thing an external developer reads** when they start building a connector.

It does almost nothing on purpose: take a `name`, generate one or more `"Hello, {name}!"` records, and return a summary. What it *does* do is exercise every piece of the SDK you need for a real connector — typed contracts, `@task` orchestration, the local dev server, unit + SDR tests, the Pkl-driven UI manifest, the production Dockerfile — in the cleanest possible shape.

Use it as a template: copy the repo, rename `hello-world` → `your-connector`, swap the two tasks for your real extract + transform, and you're 80 % of the way to a connector PR.

---

## What it does

```
HelloWorldInput (name, repeat_count)
        │
        ▼
┌────────────────────────────┐
│  @task generate_greetings  │   → writes greetings.jsonl
└────────────────────────────┘
        │
        ▼
┌────────────────────────────┐
│  @task summarize           │   → reads JSONL, returns last message
└────────────────────────────┘
        │
        ▼
HelloWorldOutput (message, record_count, output_file)
```

Two tasks, one workflow, one typed input, one typed output. Nothing else.

---

## Repo layout

```
atlan-hello-world-app/
├── README.md                  ← you are here
├── pyproject.toml             ← uv project; pins atlan-application-sdk
├── Dockerfile                 ← extends registry.atlan.com/public/app-runtime-base:3
├── atlan.yaml                 ← App manifest (execution_mode, dapr, keda)
├── app.yaml                   ← image binding for deployment
├── Makefile                   ← generate / test / run / lint
├── .env.example               ← documented dev env vars (copy to .env)
├── .pre-commit-config.yaml    ← ruff + pyright
├── main.py                    ← container entry point
├── contract/
│   ├── app.pkl                ← canonical input + UI schema
│   ├── PklProject             ← Pkl deps (app-contract-toolkit)
│   └── PklProject.deps.json
├── app/
│   ├── __init__.py
│   ├── contracts.py           ← typed Input/Output for every task
│   ├── connector.py           ← HelloWorldApp(App) + @task methods
│   ├── run_dev.py             ← local dev server
│   └── generated/             ← AUTO-GENERATED from contract/app.pkl
│       ├── _input.py
│       └── manifest.json
├── tests/
│   ├── unit/
│   │   ├── test_contracts.py  ← JSON round-trip pinning for every contract
│   │   └── test_connector.py  ← task bodies tested with a fake context
│   └── sdr/
│       └── test_hello_world_sdr.py  ← full SDR container end-to-end
└── .github/
    ├── CODEOWNERS
    └── workflows/
        ├── checks.yml                  ← pre-commit + unit tests on every PR
        └── sdr-integration-tests.yaml  ← gated on `sdr-e2e-test` PR label
```

---

## Local development

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [Temporal dev server](https://docs.temporal.io/cli#server) — `brew install temporal`

### One-time setup

```bash
uv sync --all-extras
cp .env.example .env   # optional, tweak if you want
```

### Run the dev server

```bash
# Terminal 1: Temporal
temporal server start-dev \
  --dynamic-config-value frontend.WorkerHeartbeatsEnabled=true

# Terminal 2: the app
make run    # alias for: uv run python -m app.run_dev
```

The HTTP handler listens on `http://localhost:8000` and the Temporal worker connects automatically.

### Trigger a workflow

```bash
curl -X POST http://localhost:8000/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{"name": "Atlan", "repeat_count": 3}'

# → {"success": true, "data": {"workflow_id": "...", "run_id": "..."}, ...}

# Fetch the result (use the workflow_id from above):
curl http://localhost:8000/workflows/v1/result/<workflow_id>
```

---

## Tests

```bash
make test           # unit tests (fast, no Temporal needed)
make test-all       # everything, including SDR (needs the container)
```

- **Unit tests** (`tests/unit/`) call `@task` bodies directly with a fake `AppContext`. Fast, hermetic, run on every PR.
- **SDR tests** (`tests/sdr/`) start the customer-style SDR container, submit a workflow over HTTP, and poll for `COMPLETED`. They run in CI when a PR carries the `sdr-e2e-test` label.

---

## Evolving the input schema

The top-level workflow input lives in **one** place: [`contract/app.pkl`](contract/app.pkl). The Atlan UI form and the Python typed dataclass are both generated from it.

```bash
# After editing contract/app.pkl:
make generate          # regenerates app/generated/_input.py + manifest.json
make check-generate    # CI guard: fails if generated files are stale
```

`pkl` is the only extra tool you need — install it from <https://pkl-lang.org>.

---

## Building the container

```bash
docker build -t atlan-hello-world-app:dev .

# Run it standalone (same as production):
docker run --rm -p 8000:8000 \
  -e ATLAN_TEMPORAL_HOST=host.docker.internal:7233 \
  atlan-hello-world-app:dev
```

The base image (`registry.atlan.com/public/app-runtime-base:3`) brings `uv`, a non-root `appuser`, and the SDK runtime entrypoint — your Dockerfile stays a dozen lines.

---

## Making this *your* connector

1. **Rename.** Replace `hello-world` / `HelloWorldApp` / `atlan-hello-world-app` everywhere. The grep targets are: `pyproject.toml`, `atlan.yaml`, `app.yaml`, `Dockerfile`, `main.py`, `app/connector.py`, `app/run_dev.py`, `contract/app.pkl`, `app/generated/manifest.json`, `.github/workflows/sdr-integration-tests.yaml`, this README.
2. **Define your input.** Edit `contract/app.pkl`, then `make generate`.
3. **Write your tasks.** Replace `generate_greetings` and `summarize` in `app/connector.py`. Keep the shape: one `Input` in, one `Output` out, side-effects only inside `@task`-decorated methods.
4. **Pin contracts.** Add a round-trip test to `tests/unit/test_contracts.py` for every new Input/Output dataclass.
5. **Add an SDR scenario.** Drop a new `Scenario(...)` into `tests/sdr/test_hello_world_sdr.py` for each end-to-end path you care about.

---

## What's intentionally absent

To keep this reference readable, the following — present in production Atlan connectors — has been omitted:

- **Credentials.** Add a credential model (`app/credentials.py`) and register it with `register_credential_type` when your source needs auth. See `atlan-openapi-app` for a worked example.
- **`publish-app` handoff.** This app does not load assets into Atlan. Add an `upload` step (`self.upload(UploadInput(...))`) and the `transformed_data_prefix` output field once you have real assets to publish.
- **Heavy CI.** Workflows like Snyk scanning, Dependabot cooldown, release gates, and the auto-fix bot are part of the Atlan-internal repo template, not the SDK. Add them as you go.

The rest — App, `@task`, contracts, Pkl, Dockerfile, atlan.yaml, run_dev, unit + SDR tests — is everything a connector actually needs.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
