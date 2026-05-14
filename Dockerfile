# syntax=docker/dockerfile:1
# Dockerfile for atlan-hello-world-app.
#
# Extends the Atlan app-runtime base image with the hello-world app code
# and its locked Python dependencies. The base image already ships uv,
# a non-root `appuser`, and the SDK runtime entrypoint.
#
# Build:
#   docker build -t atlan-hello-world-app:latest .
#
# Run (combined HTTP + Temporal worker):
#   docker run --rm -p 8000:8000 atlan-hello-world-app:latest

FROM registry.atlan.com/public/app-runtime-base:3

ARG APP_MODULE=app.connector:HelloWorldApp

WORKDIR /app

# Install locked dependencies first so the layer caches across code edits.
COPY --chown=appuser:appuser pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv venv .venv && \
    uv sync --locked --no-install-project --no-dev

# Copy application code.
COPY --chown=appuser:appuser app/ app/

ENV ATLAN_APP_MODULE=${APP_MODULE}
ENV ATLAN_CONTRACT_GENERATED_DIR=/app/app/generated
