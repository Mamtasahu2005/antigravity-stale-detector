# Minimal Bifrost gateway image for the Antigravity demo.
# File-only config => no database, no persistent disk needed.
FROM docker.io/maximhq/bifrost:latest

COPY config.json /app/data/config.json

ENV APP_HOST=0.0.0.0 \
    APP_PORT=8080 \
    APP_DIR=/app/data

EXPOSE 8080
