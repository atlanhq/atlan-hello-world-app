"""Local development server for atlan-hello-world-app.

Boots the SDK's combined HTTP handler + Temporal worker in a single process.
The handler listens on ``http://localhost:8000`` and accepts workflow start
requests; the worker picks them up from the local Temporal dev server.

Prerequisites
-------------
1. Install dependencies:    ``uv sync``
2. Start Temporal:          ``temporal server start-dev \\
                                --dynamic-config-value frontend.WorkerHeartbeatsEnabled=true``
3. (Optional) copy ``.env.example`` to ``.env`` and tweak.

Run
---
::

    uv run python -m app.run_dev

Trigger a workflow
------------------
::

    curl -X POST http://localhost:8000/workflows/v1/start \\
      -H "Content-Type: application/json" \\
      -d '{"name": "Atlan", "repeat_count": 3}'

    # The response contains workflow_id + run_id. Fetch the result:
    curl http://localhost:8000/workflows/v1/result/<workflow_id>
"""

import asyncio
import os

from application_sdk.main import run_dev_combined

from app.connector import HelloWorldApp


async def main() -> None:
    """Run the dev server with sensible defaults for an empty .env."""
    default_name = os.environ.get("HELLO_WORLD_DEFAULT_NAME", "World")
    repeat_count = int(os.environ.get("HELLO_WORLD_REPEAT_COUNT", "1"))

    await run_dev_combined(
        HelloWorldApp,
        example_input={
            "name": default_name,
            "repeat_count": repeat_count,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
