"""Behavioural tests for HelloWorldApp tasks.

The ``@task`` decorator does not wrap the function — it just attaches metadata.
Outside the workflow runtime the methods execute as ordinary coroutines,
which is exactly what we want for fast unit tests: we exercise the real input/
output contracts and on-disk side effects with no external services.
"""

from __future__ import annotations

import logging
from pathlib import Path

import orjson
import pytest
from application_sdk.contracts.types import FileReference
from application_sdk.errors import InvalidInputError

from app.connector import HelloWorldApp
from app.contracts import (
    GenerateGreetingsInput,
    SummarizeInput,
)


class _FakeContext:
    """Stand-in for ``AppContext`` — only ``logger`` and ``run_id`` are read."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("hello-world.test")
        self.run_id = "test-run-id"


@pytest.fixture
def hello_app() -> HelloWorldApp:
    app = HelloWorldApp()
    app._context = _FakeContext()  # type: ignore[assignment]
    return app


class TestGenerateGreetings:
    async def test_writes_one_record_by_default(
        self, hello_app: HelloWorldApp, tmp_path: Path
    ) -> None:
        out = await hello_app.generate_greetings(
            GenerateGreetingsInput(name="World", repeat_count=1, output_dir=str(tmp_path)),
        )
        assert out.record_count == 1
        assert out.greetings_file is not None
        records = _read_jsonl(Path(out.greetings_file.local_path))
        assert records == [{"index": 0, "message": "Hello, World!"}]

    async def test_repeat_count_writes_n_records(
        self, hello_app: HelloWorldApp, tmp_path: Path
    ) -> None:
        out = await hello_app.generate_greetings(
            GenerateGreetingsInput(name="Atlan", repeat_count=4, output_dir=str(tmp_path)),
        )
        records = _read_jsonl(Path(out.greetings_file.local_path))
        assert len(records) == 4
        assert all(r["message"] == "Hello, Atlan!" for r in records)
        assert [r["index"] for r in records] == [0, 1, 2, 3]

    async def test_repeat_count_zero_raises(self, hello_app: HelloWorldApp, tmp_path: Path) -> None:
        with pytest.raises(InvalidInputError):
            await hello_app.generate_greetings(
                GenerateGreetingsInput(name="World", repeat_count=0, output_dir=str(tmp_path)),
            )


class TestSummarize:
    async def test_summarises_records(self, hello_app: HelloWorldApp, tmp_path: Path) -> None:
        path = tmp_path / "greetings.jsonl"
        path.write_bytes(b'{"index":0,"message":"Hello, A!"}\n{"index":1,"message":"Hello, A!"}\n')

        out = await hello_app.summarize(
            SummarizeInput(greetings_file=FileReference(local_path=str(path))),
        )
        assert out.message == "Hello, A!"
        assert out.record_count == 2

    async def test_missing_file_raises(self, hello_app: HelloWorldApp) -> None:
        with pytest.raises(InvalidInputError):
            await hello_app.summarize(
                SummarizeInput(greetings_file=FileReference(local_path="/does/not/exist.jsonl")),
            )


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_bytes().splitlines():
        if line.strip():
            out.append(orjson.loads(line))
    return out
