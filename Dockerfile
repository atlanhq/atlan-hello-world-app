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
# Production deploy: pushed by CI; the Atlan platform schedules it from
# `atlan.yaml`. For local iteration use `make run` instead.

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
