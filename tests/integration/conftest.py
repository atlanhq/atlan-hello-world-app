"""Integration-tier fixtures for atlan-hello-world-app.

Adopts the SDK's canonical integration fixture kit
(``application_sdk.testing.integration.fixtures``), documented in the SDK's
``docs/guides/integration-fixtures.md``. The star-import brings in the kit
fixtures — ``store_root``, ``temporary_path``, ``infrastructure``,
``embedded_temporal``, ``temporal_client``, ``worker``, ``executor`` — plus the
``integration_*`` override points. The App then runs for real: an embedded
Temporal dev server, mocked secret/state stores over a local object store, a
real worker, and submission through the real data converter.

Only ``integration_app_cls`` is overridden. hello-world extracts from nothing
external, so the kit's default ``integration_source`` of ``None`` — and the
empty ``integration_secrets`` that follows from it — is already correct: there
is no container to start and no credential to seed.

The ``os.environ.setdefault`` calls must stay above the imports, and this is the
one thing to preserve when editing this file. Importing anything under
``application_sdk`` snapshots these values into ``application_sdk.constants``,
so an import hoisted above them would bind the wrong ones. The kit checks the
snapshot against the live environment when it loads and raises
``IntegrationEnvOrderingError`` if they disagree, which surfaces as a collection
error failing every test rather than as a subtly mistagged run.

Ruff's import rules do not fight this: ``I`` sorts only within a contiguous
import block, and ``E402`` does not fire on module-level statements of this
shape, so no suppression is needed to keep the order.
"""

import os

os.environ.setdefault("ATLAN_APPLICATION_NAME", "hello-world")
os.environ.setdefault("ATLAN_DEPLOYMENT_NAME", "ci")

import pytest
from application_sdk.testing.integration.fixtures import *  # noqa: F403

from app.connector import HelloWorldApp


@pytest.fixture(scope="session")
def integration_app_cls() -> type[HelloWorldApp]:
    """The App class the kit's worker registers and the executor submits to."""
    return HelloWorldApp
