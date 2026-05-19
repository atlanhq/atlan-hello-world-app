# AUTO-GENERATED from app.pkl — DO NOT EDIT MANUALLY.
# To regenerate: make generate
from __future__ import annotations

from application_sdk.templates.contracts import ExtractionInput


class AppInputContract(ExtractionInput):
    name: str = ""
    """Who should the workflow greet?"""
    repeat_count: int = 1
    """How many greeting records to generate."""
