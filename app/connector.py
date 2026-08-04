"""Hello World connector App.

Demonstrates the canonical Atlan Application SDK pattern with the simplest
possible domain (no external system, no credentials):

1. ``generate_greetings`` task — pure-Python "extract" that writes a JSONL
   file with one record per requested greeting. Replace this with your real
   extract step (HTTP call, SQL query, file read, …).
2. ``summarize`` task — reads the JSONL back and returns a single message.
   Stands in for the "transform" / "load" steps a real connector would have.
3. ``run`` orchestrates the two tasks deterministically. Only ``@task``
   methods may do I/O — ``run`` must stay replay-safe.

Read alongside ``contracts.py``: every task takes one ``Input`` subclass and
returns one ``Output`` subclass, so the runtime can serialise the boundary
and schema evolution stays safe.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import orjson
from application_sdk.app import App, task
from application_sdk.contracts.types import FileReference, StorageTier

from app.contracts import (
    GenerateGreetingsInput,
    GenerateGreetingsOutput,
    HelloWorldInput,
    HelloWorldOutput,
    SummarizeInput,
    SummarizeOutput,
)
from app.errors import GreetingsFileMissingError, InvalidRepeatCountError

# Shared @task timeout budget for this app's tasks. heartbeat_timeout is kept
# an order of magnitude below timeout_seconds (not ~50%, as it was before)
# so a transient event-loop stall can't trip a heartbeat timeout well before
# the activity's actual start-to-close budget is spent (HB-10). Defined once
# and reused by both tasks below so the ratio can't drift out of sync between
# them.
_TASK_TIMEOUT_SECONDS = 300
_TASK_HEARTBEAT_TIMEOUT_SECONDS = 30
_TASK_AUTO_HEARTBEAT_SECONDS = 10


class HelloWorldApp(App):
    """The minimum-viable Atlan App.

    ``name`` is the workflow type the SDK registers with its runtime — it
    must match ``contract/app.pkl`` and ``atlan.yaml`` so the deployed task
    queue (``atlan-hello-world-{deployment}``) routes work to this App.
    """

    name = "hello-world"

    @task(
        timeout_seconds=_TASK_TIMEOUT_SECONDS,
        heartbeat_timeout_seconds=_TASK_HEARTBEAT_TIMEOUT_SECONDS,
        auto_heartbeat_seconds=_TASK_AUTO_HEARTBEAT_SECONDS,
    )
    async def generate_greetings(self, input: GenerateGreetingsInput) -> GenerateGreetingsOutput:
        """Write ``input.repeat_count`` greetings as JSONL.

        Real connectors put their HTTP / SQL / object-store I/O here.
        """
        if input.repeat_count < 1:
            raise InvalidRepeatCountError(value_summary=str(input.repeat_count))

        out_dir = Path(tempfile.mkdtemp(prefix="hello-world-"))
        out_path = out_dir / "greetings.jsonl"

        self.logger.info(
            "generate_greetings starting name=%s repeat_count=%d",
            input.name,
            input.repeat_count,
        )

        with out_path.open("wb") as f:
            for i in range(input.repeat_count):
                record = {"index": i, "message": f"Hello, {input.name}!"}
                f.write(orjson.dumps(record) + b"\n")

        self.logger.info(
            "generate_greetings completed record_count=%d output=%s",
            input.repeat_count,
            out_path,
        )

        return GenerateGreetingsOutput(
            greetings_file=FileReference(local_path=str(out_path), tier=StorageTier.RETAINED),
            record_count=input.repeat_count,
        )

    @task(
        timeout_seconds=_TASK_TIMEOUT_SECONDS,
        heartbeat_timeout_seconds=_TASK_HEARTBEAT_TIMEOUT_SECONDS,
        auto_heartbeat_seconds=_TASK_AUTO_HEARTBEAT_SECONDS,
    )
    async def summarize(self, input: SummarizeInput) -> SummarizeOutput:
        """Read greetings JSONL and produce a one-line summary."""
        greetings_file = self.require(input.greetings_file, "greetings_file")
        path = Path(greetings_file.local_path or "")
        if not path.exists():
            raise GreetingsFileMissingError(value_summary=str(path))

        last_message = ""
        record_count = 0
        with path.open("rb") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = orjson.loads(line)
                last_message = record.get("message", "")
                record_count += 1

        message = last_message or "Hello!"
        self.logger.info("summarize completed record_count=%d message=%s", record_count, message)
        return SummarizeOutput(message=message, record_count=record_count)

    async def run(self, input: HelloWorldInput) -> HelloWorldOutput:  # type: ignore[override]
        """Orchestrate generate_greetings → summarize.

        ``run`` is the workflow function — it must be deterministic so the
        SDK can replay it on retry. Anything that touches the outside world
        (network, disk, clock) lives inside a ``@task`` method, never here.
        """
        self.logger.info(
            "hello-world workflow starting name=%s repeat_count=%d",
            input.name,
            input.repeat_count,
        )

        greetings = await self.generate_greetings(
            GenerateGreetingsInput(
                name=input.name,
                repeat_count=input.repeat_count,
            )
        )

        summary = await self.summarize(SummarizeInput(greetings_file=greetings.greetings_file))

        self.logger.info(
            "hello-world workflow completed message=%s record_count=%d",
            summary.message,
            summary.record_count,
        )

        return HelloWorldOutput(
            message=summary.message,
            record_count=summary.record_count,
            output_file=greetings.greetings_file,
        )
