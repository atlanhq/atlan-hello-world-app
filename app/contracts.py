"""Typed Input/Output contracts for the Hello World app.

Every dataclass that crosses a workflow boundary extends ``Input`` /
``Output`` from ``application_sdk.contracts``. Each ``@task`` method on the
connector takes exactly one ``Input`` subclass and returns exactly one
``Output`` subclass — this is what makes workflow replay and schema
evolution safe.

The top-level app input is auto-generated from ``contract/app.pkl`` into
``app/generated/_input.py``. Edit the Pkl file and re-run ``make generate``
to evolve the schema; never hand-edit the generated file.
"""

from application_sdk.app import Input, Output
from application_sdk.contracts.types import FileReference

from app.generated._input import AppInputContract

# =============================================================================
# Top-level App input / output
# =============================================================================

HelloWorldInput = AppInputContract


class HelloWorldOutput(Output):
    """Final result returned to the caller of the workflow."""

    message: str = ""
    """The greeting message that was produced (e.g. ``"Hello, World!"``)."""

    record_count: int = 0
    """Number of greeting records the workflow generated."""

    output_file: FileReference | None = None
    """Local path to the JSONL file the workflow wrote, if any."""


# =============================================================================
# Task-level contracts: generate_greetings
# =============================================================================


class GenerateGreetingsInput(Input):
    """Input for the ``generate_greetings`` task."""

    name: str = "World"
    """Name to greet — substituted into the greeting template."""

    repeat_count: int = 1
    """How many greeting records to emit. Must be >= 1."""


class GenerateGreetingsOutput(Output):
    """Output from the ``generate_greetings`` task."""

    greetings_file: FileReference | None = None
    """JSONL file containing one greeting record per line."""

    record_count: int = 0
    """Number of records written to ``greetings_file``."""


# =============================================================================
# Task-level contracts: summarize
# =============================================================================


class SummarizeInput(Input):
    """Input for the ``summarize`` task."""

    greetings_file: FileReference | None = None
    """JSONL produced by ``generate_greetings``."""


class SummarizeOutput(Output):
    """Output from the ``summarize`` task."""

    message: str = ""
    """Human-readable summary of the run — surfaced in the workflow output."""

    record_count: int = 0
    """Number of records the summary counted."""
