# atlan-hello-world-app

The smallest, end-to-end Atlan app — built on the [Application SDK](https://github.com/atlanhq/application-sdk) — designed as the **first thing an external developer reads** when they start building a connector.

It does almost nothing on purpose: take a `name`, generate one or more `"Hello, {name}!"` records, and return a summary. What it *does* do is exercise every piece of the SDK you need for a real connector — typed contracts, `@task` orchestration, the local dev server, unit tests, the Pkl-driven UI manifest, the production Dockerfile — in the cleanest possible shape.

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
├── atlan.yaml                 ← App manifest (execution_mode, runtime config)
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
│   └── unit/
│       ├── test_contracts.py  ← JSON round-trip pinning for every contract
│       └── test_connector.py  ← task bodies tested with a fake context
└── .github/
    ├── CODEOWNERS
    └── workflows/
        └── checks.yml                  ← pre-commit + unit tests on every PR
```

---

## Local development

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

That's it. Everything else — the workflow runtime, the Dapr sidecar, the
HTTP handler, the worker — is brought up by `application-sdk` itself.

### Step 1 — install dependencies

```bash
uv sync --all-extras
```

- Reads `pyproject.toml` + `uv.lock`.
- Creates a `.venv/` in the repo.
- Installs Python dependencies into it (including `atlan-application-sdk`
  and its transitive deps like `temporalio`, `obstore`, etc.).
- One-time setup. Re-run only if you change `pyproject.toml` or pull a new
  lockfile.

### Step 2 — (optional) tweak environment

```bash
cp .env.example .env
```

The dev server runs with sensible defaults; only copy if you need to
override one of the variables in `.env.example`.

### Step 3 — run the dev server

```bash
uv run python -m app.run_dev
```

- Activates the `.venv` (implicit via `uv run`).
- Imports `HelloWorldApp` and calls `run_dev_combined(HelloWorldApp, …)`.
- The SDK does the rest: spawns an embedded `daprd` sidecar (downloads it
  on first run, ~50 MB cached in `~/.cache/atlan-sdk/dapr/`), spawns an
  embedded Temporal dev-server (~30 MB cached in `~/.cache/temporalio/`),
  starts the HTTP handler on `:8000`, starts the worker, registers the
  workflow.
- Runs in the foreground; `Ctrl-C` to stop (both daemons are SIGTERM'd
  cleanly, the temp components directory is removed).

The first invocation takes ~30 s while the binaries download. Every
invocation after that is instant.

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
uv run pytest tests/unit -q
```

Unit tests in `tests/unit/` call `@task` bodies directly with a fake
`AppContext`. Fast, hermetic, run on every PR via `.github/workflows/checks.yml`.

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
```

The base image (`registry.atlan.com/public/app-runtime-base:3`) brings `uv`, a non-root `appuser`, and the SDK runtime entrypoint — your Dockerfile stays a dozen lines. The deployed container connects to the runtime configured in your `atlan.yaml`; for local iteration use `make run` instead.

---

## What is `atlan.yaml` and `app.yaml`?

Two small files, two distinct jobs:

- **`atlan.yaml`** — the **app manifest**. Declares the app's identity (`name`, `display_name`, `type`, `visibility`), how it runs (`execution_mode`, KEDA autoscaling, timeouts), and which platform components it needs. The Atlan platform reads this when deploying the app.
- **`app.yaml`** — the **image binding**. Just `app_name`, `app_image` (templated as `${APP_IMAGE}` and filled in by CI), and `app_port`. It's the deployment-time link between a built container and the manifest.

You almost never edit `app.yaml`. You edit `atlan.yaml` when you add a real I/O surface (object storage, secrets, autoscaling rules).

---

## Making this *your* connector

1. **Rename.** Replace `hello-world` / `HelloWorldApp` / `atlan-hello-world-app` everywhere. The grep targets are: `pyproject.toml`, `atlan.yaml`, `app.yaml`, `Dockerfile`, `main.py`, `app/connector.py`, `app/run_dev.py`, `contract/app.pkl`, `app/generated/manifest.json`, this README.
2. **Define your input.** Edit `contract/app.pkl`, then `make generate`.
3. **Write your tasks.** Replace `generate_greetings` and `summarize` in `app/connector.py`. Keep the shape: one `Input` in, one `Output` out, side-effects only inside `@task`-decorated methods.
4. **Pin contracts.** Add a round-trip test to `tests/unit/test_contracts.py` for every new Input/Output dataclass.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
