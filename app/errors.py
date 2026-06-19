"""Domain-specific typed error leaves for the hello-world connector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from application_sdk.errors import InvalidInputError


@dataclass(kw_only=True)
class InvalidRepeatCountError(InvalidInputError):
    """repeat_count is below the minimum allowed value."""

    code: ClassVar[str] = "INVALID_INPUT_REPEAT_COUNT"
    message: str = "repeat_count must be >= 1"
    field: str | None = "repeat_count"
    constraint: str | None = ">= 1"


@dataclass(kw_only=True)
class GreetingsFileMissingError(InvalidInputError):
    """Greetings JSONL file not found at the expected local path."""

    code: ClassVar[str] = "INVALID_INPUT_GREETINGS_FILE_MISSING"
    message: str = "greetings_file does not exist"
    field: str | None = "greetings_file"
    constraint: str | None = "file must exist"
