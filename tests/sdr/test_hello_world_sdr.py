"""SDR integration tests for atlan-hello-world-app.

Runs the app inside a customer-style SDR container — the same image and
runtime an Atlan tenant would deploy — and submits a workflow over HTTP.

The SDK provides ``BaseSDRIntegrationTest`` which handles container readiness,
workflow polling, and assertion DSL. The CI workflow in
``.github/workflows/sdr-integration-tests.yaml`` builds the image and stands
the container up before this test runs.

To run locally, first start the SDR stack with the SDK's composite action,
then::

    uv run pytest tests/sdr -q
"""

from __future__ import annotations

from typing import Any, ClassVar

from application_sdk.testing.integration import (
    Scenario,
    equals,
    is_not_empty,
)
from application_sdk.testing.sdr import BaseSDRIntegrationTest


class TestHelloWorldSdr(BaseSDRIntegrationTest):
    """Single happy-path scenario: greet "Atlan" twice and confirm COMPLETED."""

    agent_spec_template: ClassVar[dict[str, Any]] = {}
    timeout: int = 60

    default_credentials: ClassVar[dict[str, Any]] = {}
    default_metadata: ClassVar[dict[str, Any]] = {}
    default_connection: ClassVar[dict[str, Any]] = {}

    def _build_scenario_args(self, scenario: Scenario) -> dict[str, Any]:
        # The app's input contract takes top-level ``name`` and ``repeat_count``.
        # The base class nests scenario inputs under ``metadata`` by default —
        # flatten so the request body matches the contract shape.
        args = super()._build_scenario_args(scenario)
        metadata = args.pop("metadata", {})
        args.update(metadata)
        return args

    scenarios: ClassVar[list[Scenario]] = [
        Scenario(
            name="greet_atlan",
            api="workflow",
            metadata={"name": "Atlan", "repeat_count": 2},
            assert_that={
                "success": equals(True),
                "data.workflow_id": is_not_empty(),
                "data.run_id": is_not_empty(),
            },
            workflow_timeout=120,
            polling_interval=5,
            description=(
                "Submit a hello-world workflow and poll for COMPLETED inside "
                "the SDR container. Validates the full extract → summarize "
                "pipeline end-to-end."
            ),
        ),
    ]
