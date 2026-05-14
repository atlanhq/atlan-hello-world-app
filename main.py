"""Production entry point for atlan-hello-world-app.

In container deployments the SDK runtime imports the App class declared in
the ``ATLAN_APP_MODULE`` env var and boots a combined HTTP handler + Temporal
worker. This thin script provides the same behaviour when running the image
directly (``docker run …`` without overriding the command).

For local development with example payloads, use ``python -m app.run_dev``.
"""

import asyncio

from app.run_dev import main

if __name__ == "__main__":
    asyncio.run(main())
