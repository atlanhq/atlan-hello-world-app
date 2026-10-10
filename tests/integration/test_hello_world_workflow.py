"""Integration tier: the hello-world workflow, executed end to end.

What separates this from ``tests/unit`` is the runtime, not the assertions.
The unit tier calls the ``@task`` coroutines directly, so it never exercises
the workflow boundary. Here the App is registered on a real worker against an
embedded Temporal dev server, and the input and output cross that boundary
through the App's own data converter — so a contract that fails to serialise
fails here and nowhere else.

hello-world has no external system to extract from, so the run is hermetic:
the SDK fixture kit supplies mocked secret/state stores over a local object
store, and no source fixture is needed.
"""

from __future__ import annotations

from pathlib import Path

import orjson
import pytest
from application_sdk.execution.settings import load_interceptor_settings
from application_sdk.testing.integration.fixtures import AppExecutor

from app.connector import HelloWorldApp
from app.contracts import HelloWorldInput

#: Deselects this module from the unit job, which runs ``tests/unit`` only.
#: Conformance rule T001 requires it on every test under ``tests/integration``.
pytestmark = pytest.mark.integration


async def test_workflow_produces_greetings_end_to_end(executor: AppExecutor) -> None:
    """A full run returns the summary its own extract wrote."""
    output = await executor.execute_app(
        HelloWorldApp,
        HelloWorldInput(name="Atlan", repeat_count=3),
    )

    assert output.message == "Hello, Atlan!"
    assert output.record_count == 3


async def test_workflow_writes_the_greetings_file(
    executor: AppExecutor,
    store_root: Path,
) -> None:
    """The ``FileReference`` returned by the run points at a real JSONL file.

    Asserting on the artifact rather than only the summary is what proves the
    two tasks were chained through the workflow: ``summarize`` counted records
    that ``generate_greetings`` had actually written to disk.

    The file is read from the object store at the ref's ``storage_path`` — the
    durable ``RETAINED`` copy a consumer downloads — not from ``local_path``,
    which is task scratch that ``App.on_complete()`` cleanup deletes.
    """
    output = await executor.execute_app(
        HelloWorldApp,
        HelloWorldInput(name="World", repeat_count=2),
    )

    assert output.output_file is not None
    assert output.output_file.storage_path
    greetings_path = store_root / output.output_file.storage_path
    assert greetings_path.is_file(), f"No durable greetings file at {greetings_path}"

    records = [
        orjson.loads(line) for line in greetings_path.read_bytes().splitlines() if line.strip()
    ]
    assert [record["message"] for record in records] == [
        "Hello, World!",
        "Hello, World!",
    ]
    assert [record["index"] for record in records] == [0, 1]


async def test_local_greetings_file_cleaned_up(executor: AppExecutor) -> None:
    """The local copy is scratch: ``App.on_complete()`` cleanup deletes it.

    Pins the production behaviour — only the object-store copy outlives a run,
    so downstream code must read ``storage_path``, never ``local_path``.
    """
    if not load_interceptor_settings().enable_cleanup_interceptor:
        pytest.skip("Cleanup disabled by APPLICATION_SDK_ENABLE_CLEANUP_INTERCEPTOR")

    output = await executor.execute_app(
        HelloWorldApp,
        HelloWorldInput(name="World", repeat_count=1),
    )

    assert output.output_file is not None
    assert output.output_file.local_path
    assert not Path(output.output_file.local_path).exists(), (
        f"Local scratch survived cleanup: {output.output_file.local_path}"
    )
