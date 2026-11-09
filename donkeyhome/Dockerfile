# Home Assistant's own Alpine + Python base image (multi-arch: amd64 and aarch64).
FROM ghcr.io/home-assistant/base-python:3.14-alpine3.24

ARG BUILD_ARCH
ARG BUILD_VERSION

COPY app /app
WORKDIR /app
# with-contenv: s6 hands the container environment (SUPERVISOR_TOKEN) to the app.
CMD ["/command/with-contenv", "python3", "-u", "/app/server.py"]
