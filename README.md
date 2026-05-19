# atlan-hello-world-app

A minimal, runnable **Atlan app** you can clone, modify, and use as the
skeleton for your own. It does the smallest thing an Atlan app can do — take
a name, generate `"Hello, {name}!"` records, return a summary — so you can
focus on learning the shape of an Atlan app, not the business logic.

If you're here to build an integration that pulls metadata from your system
into Atlan, **start with this repo**, get it running locally in two commands,
then replace the toy logic with your real extraction.

---

## What's an Atlan app?

An Atlan app is a small service that runs on the Atlan platform and does
something useful with the metadata graph — pulling in metadata from a
source system, publishing it back out, transforming or enriching it,
reacting to events, automating a workflow.

The [`application-sdk`](https://github.com/atlanhq/application-sdk) is the
Python library Atlan provides for writing those workflows. This repo is
the "hello world" example built on top of it.

---

## Try it in 30 seconds

You need **Python 3.11+** and [**`uv`**](https://github.com/astral-sh/uv).
The SDK handles everything else for you.

```bash
git clone https://github.com/atlanhq/atlan-hello-world-app.git
cd atlan-hello-world-app
uv sync                         # one-time: install deps
uv run python -m app.run_dev    # boots the dev server on :8000
```

The first run takes ~30 s while the SDK fetches the runtime binaries it
needs (cached locally — subsequent runs are instant).

In a second terminal:

```bash
# Start a workflow
curl -X POST http://localhost:8000/workflows/v1/start \
  -H "Content-Type: application/json" \
  -d '{"name": "Atlan", "repeat_count": 3}'
# → {"success": true, "data": {"workflow_id": "hello-world-...", ...}}

# Fetch the result (use the workflow_id from the response above)
curl http://localhost:8000/workflows/v1/result/<workflow_id>
# → {"data": {"status": "completed",
#             "result": {"message": "Hello, Atlan!", "record_count": 3, ...}}}
```

If you see `Hello, Atlan!` come back, the app ran end-to-end. Hit
`Ctrl-C` in the first terminal to stop it.

---

## How it works

The whole app is **two tasks chained into one workflow**:

```
                  ┌──────────────────────┐
input ──────────▶ │  generate_greetings  │ ──── writes greetings.jsonl
{name,            └──────────────────────┘
 repeat_count}                │
                              ▼
                  ┌──────────────────────┐
                  │      summarize       │ ──── reads file, picks last record
                  └──────────────────────┘
                              │
                              ▼
                       {message, count, output_file}
```

Each task is just a Python `async` method on a class:

```python
class HelloWorldApp(App):
    name = "hello-world"

    @task(timeout_seconds=60)
    async def generate_greetings(self, input: GenerateGreetingsInput
                                 ) -> GenerateGreetingsOutput:
        # ... your I/O here: HTTP call, SQL query, file read, anything ...
        return GenerateGreetingsOutput(...)

    @task(timeout_seconds=60)
    async def summarize(self, input: SummarizeInput) -> SummarizeOutput:
        # ... transform / aggregate ...
        return SummarizeOutput(...)

    async def run(self, input: HelloWorldInput) -> HelloWorldOutput:
        # Orchestrates the tasks. Deterministic — no side effects here.
        greetings = await self.generate_greetings(...)
        summary   = await self.summarize(...)
        return HelloWorldOutput(...)
```

Three rules to keep in mind:

1. **All I/O — network, disk, time — happens inside `@task` methods.**
   The `run()` method must stay deterministic so the SDK can replay it
   safely on retry.
2. **Every task takes one typed `Input` and returns one typed `Output`.**
   These are simple Pydantic-style dataclasses defined in `app/contracts.py`.
3. **The top-level workflow input** (the JSON body of `POST /workflows/v1/start`)
   is generated from a single source — `contract/app.pkl` — so the Atlan
   UI form and the Python dataclass can't drift apart.

That's the entire programming model. Open `app/connector.py` to see the
whole thing in ~150 lines.

---

## Make it your own

The smallest path from this repo to a real connector:

1. **Rename.** Replace `hello-world` / `HelloWorldApp` / `atlan-hello-world-app`
   with your connector's identifiers. Files to touch: `pyproject.toml`,
   `atlan.yaml`, `app.yaml`, `Dockerfile`, `main.py`, `app/connector.py`,
   `app/run_dev.py`, `contract/app.pkl`, `app/generated/manifest.json`,
   this README.
2. **Describe your inputs.** Edit `contract/app.pkl` — what fields will
   your Atlan UI form ask the user for? Then run `make generate` to
   regenerate the typed dataclass and the UI manifest.
3. **Write your real tasks.** Replace `generate_greetings` (your *extract*)
   and `summarize` (your *transform*) in `app/connector.py`. Keep the
   shape: one `@task` per discrete step, one `Input` in, one `Output` out.
4. **Pin the contract.** Add a round-trip test to
   `tests/unit/test_contracts.py` for every new `Input` / `Output` you
   define, so a future schema change can't silently break compatibility.

When all four are done you have a working Atlan connector. Open a PR and
the Atlan team can walk through deployment.

---

## Tests

```bash
uv run pytest tests/unit -q
```

The tests call `@task` methods directly with a fake context — no SDK
runtime needed. Fast, hermetic, and they run on every PR via
`.github/workflows/checks.yml`. Add tests as you add tasks.

---

## Configuration files — what they each do

You'll see a few config files in the repo. Quick reference:

| File | What it is |
|---|---|
| `pyproject.toml` | Standard Python project file — pins `atlan-application-sdk`, declares dev tools. |
| `contract/app.pkl` | Single source of truth for the connector's input schema. Regenerates the UI form + Python dataclass via `make generate`. Edit when you want to change what the Atlan UI asks users for. |
| `atlan.yaml` | The **app manifest**. Tells the Atlan platform how to deploy your connector: its name, whether it autoscales, which platform components (object storage, secrets) it needs, what timeouts apply. Edit when you add a real I/O surface. |
| `app.yaml` | The **image binding**. Just `app_name`, `app_image`, `app_port`. CI fills in the image tag at deploy time — you rarely edit this. |
| `Dockerfile` | Production container. Extends `registry.atlan.com/public/app-runtime-base:3` which ships `uv`, a non-root user, and the SDK runtime entrypoint, so this file stays a dozen lines. |
| `Makefile` | Shortcuts for the commands you'll use often: `make generate`, `make test`, `make run`, `make lint`. |
| `.env.example` | Lists the optional env vars the dev server understands. Copy to `.env` to override defaults. |

---

## Repo layout

```
atlan-hello-world-app/
├── README.md                  ← you are here
├── pyproject.toml             ← Python project + SDK pin
├── Dockerfile                 ← extends registry.atlan.com/public/app-runtime-base:3
├── atlan.yaml                 ← app manifest (deploy config)
├── app.yaml                   ← image binding (CI fills in)
├── Makefile                   ← generate / test / run / lint shortcuts
├── .env.example               ← documented dev env vars
├── .pre-commit-config.yaml    ← ruff + pyright
├── main.py                    ← container entry point
├── contract/
│   ├── app.pkl                ← canonical input + UI schema
│   ├── PklProject             ← Pkl deps (app-contract-toolkit)
│   └── PklProject.deps.json
├── app/
│   ├── contracts.py           ← typed Input/Output for every task
│   ├── connector.py           ← HelloWorldApp(App) + @task methods
│   ├── run_dev.py             ← local dev server entry point
│   └── generated/             ← AUTO-GENERATED from contract/app.pkl
│       ├── _input.py
│       └── manifest.json
├── tests/
│   └── unit/
│       ├── test_contracts.py  ← JSON round-trip pinning for every contract
│       └── test_connector.py  ← task bodies tested with a fake context
└── .github/
    └── workflows/
        └── checks.yml         ← pre-commit + unit tests on every PR
```

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `make run` hangs on first run for ~30 s | Normal — SDK is downloading the workflow runtime binaries into `~/.cache/`. Subsequent runs are instant. |
| `POST /workflows/v1/start` returns 404 | The dev server isn't up yet. Wait for `Combined mode started: …` in the dev-server log. |
| Workflow stuck in `RUNNING` | Check the dev-server log in the first terminal for the task's error message. |
| `make generate` fails with `pkl: command not found` | Install Pkl: <https://pkl-lang.org>. Only needed if you're editing `contract/app.pkl`. |

For SDK-level issues, file in
[atlanhq/application-sdk](https://github.com/atlanhq/application-sdk/issues).
For issues with this template, open one [here](https://github.com/atlanhq/atlan-hello-world-app/issues).

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
