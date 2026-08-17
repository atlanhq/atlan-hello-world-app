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
    HelloWorldInput,
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

    async def test_blank_lines_are_skipped(self, hello_app: HelloWorldApp, tmp_path: Path) -> None:
        """Blank/whitespace lines must not be counted or parsed.

        Pins the ``if not line: continue`` guard: a naive reader would feed the
        empty bytes to ``orjson.loads`` (which raises) or inflate record_count.
        """
        path = tmp_path / "greetings.jsonl"
        # Two real records separated and surrounded by blank / whitespace lines.
        path.write_bytes(
            b'\n{"index":0,"message":"Hello, A!"}\n   \n\n{"index":1,"message":"Hello, B!"}\n\n'
        )

        out = await hello_app.summarize(
            SummarizeInput(greetings_file=FileReference(local_path=str(path))),
        )
        # Only the two non-blank records count; last non-blank wins the message.
        assert out.record_count == 2
        assert out.message == "Hello, B!"

    async def test_empty_file_falls_back_to_default_message(
        self, hello_app: HelloWorldApp, tmp_path: Path
    ) -> None:
        """A file with zero records yields the ``"Hello!"`` fallback, count 0."""
        path = tmp_path / "empty.jsonl"
        path.write_bytes(b"\n   \n\n")

        out = await hello_app.summarize(
            SummarizeInput(greetings_file=FileReference(local_path=str(path))),
        )
        assert out.record_count == 0
        assert out.message == "Hello!"


class TestRun:
    """The ``run`` orchestrator: generate_greetings → summarize, wired end-to-end.

    Uses real on-disk artifacts (generate_greetings writes a JSONL that
    summarize reads back) so the ordering is pinned by data dependency: if the
    two steps ran out of order, summarize would fault on a missing file.
    """

    async def test_run_orchestrates_and_wires_output(self, hello_app: HelloWorldApp) -> None:
        out = await hello_app.run(HelloWorldInput(name="Atlan", repeat_count=3))

        # Output contract wired from BOTH sub-steps:
        #   message + record_count come from summarize, output_file from generate.
        assert out.message == "Hello, Atlan!"
        assert out.record_count == 3
        assert out.output_file is not None

        # The advertised output_file must be the real artifact generate wrote.
        assert out.output_file.local_path is not None
        records = _read_jsonl(Path(out.output_file.local_path))
        assert len(records) == 3
        assert [r["message"] for r in records] == ["Hello, Atlan!"] * 3
        assert [r["index"] for r in records] == [0, 1, 2]

    async def test_run_single_greeting_default_count(self, hello_app: HelloWorldApp) -> None:
        out = await hello_app.run(HelloWorldInput(name="World"))
        assert out.message == "Hello, World!"
        assert out.record_count == 1
        assert out.output_file is not None

    async def test_run_records_step_order(
        self, hello_app: HelloWorldApp, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """generate_greetings must run before summarize (explicit sequencing)."""
        calls: list[str] = []
        real_generate = hello_app.generate_greetings
        real_summarize = hello_app.summarize

        async def traced_generate(inp: GenerateGreetingsInput):
            calls.append("generate")
            return await real_generate(inp)

        async def traced_summarize(inp: SummarizeInput):
            calls.append("summarize")
            return await real_summarize(inp)

        monkeypatch.setattr(hello_app, "generate_greetings", traced_generate)
        monkeypatch.setattr(hello_app, "summarize", traced_summarize)

        await hello_app.run(HelloWorldInput(name="World", repeat_count=2))
        assert calls == ["generate", "summarize"]


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    for line in path.read_bytes().splitlines():
        if line.strip():
            out.append(orjson.loads(line))
    return out
