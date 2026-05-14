# AUTO-GENERATED from contract/app.pkl — DO NOT EDIT MANUALLY.
# To regenerate: make generate
from __future__ import annotations

from typing import ClassVar

from application_sdk.contracts.base import Input


class AppInputContract(Input):
    """Input contract for the hello-world app.

    Generated from ``contract/app.pkl`` so the same schema drives both the
    Atlan UI form and the Python typed input. Add new fields to the .pkl file
    and re-run ``make generate``.
    """

    _config_hash_exclude: ClassVar[set[str]] = {
        "output_dir",
    }

    name: str = "World"
    """Who should the workflow greet?"""

    repeat_count: int = 1
    """How many greeting records to generate."""

    output_dir: str = ""
    """Directory for intermediate output files. Defaults to a temp dir."""
