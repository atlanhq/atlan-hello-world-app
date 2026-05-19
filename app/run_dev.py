"""Local development server for atlan-hello-world-app.

Boots the SDK's combined HTTP handler + worker. With ``local_dev_mode=True``
the SDK brings up an in-process workflow runtime and uses in-process
backends for state/secrets/storage — no external services required.

Run::

    make run                       # or: uv run python -m app.run_dev

Trigger a workflow::

    curl -X POST http://localhost:8000/workflows/v1/start \\
      -H "Content-Type: application/json" \\
      -d '{"name": "Atlan", "repeat_count": 3}'

    # Fetch the result (use the workflow_id from the response above):
    curl http://localhost:8000/workflows/v1/result/<workflow_id>
"""

import asyncio

from application_sdk.main import run_dev_combined

from app.connector import HelloWorldApp


async def main() -> None:
    """Boot the dev runtime in-process and run the app against it."""
    await run_dev_combined(
        HelloWorldApp,
        example_input={
            "name": "World",
            "repeat_count": 1,
        },
    )


if __name__ == "__main__":
    asyncio.run(main())
