"""Test for the local development entrypoint.

``run_dev.main`` boots the SDK's in-process dev runtime. There is no external
system to reach, so we stub the SDK ``run_dev_combined`` boot call at the seam
and assert on the *contract* ``main`` hands it: the App class under test and
the example input shape a developer would POST to ``/workflows/v1/start``.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

import app.run_dev as run_dev
from app.connector import HelloWorldApp


async def test_main_boots_helloworld_with_example_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boot = AsyncMock()
    monkeypatch.setattr(run_dev, "run_dev_combined", cast(Any, boot))

    await run_dev.main()

    boot.assert_awaited_once()
    args, kwargs = boot.call_args
    # First positional arg is the App class the dev runtime should register.
    assert args[0] is HelloWorldApp
    # The example input must match the workflow's declared contract fields.
    assert kwargs["example_input"] == {"name": "World", "repeat_count": 1}
