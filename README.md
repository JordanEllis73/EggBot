# Big Green Egg Controller

Containerized project to control a servo-driven damper and read thermocouples via a microcontroller,
with a local web UI for charts and control.

## Prereqs
- Docker and Docker Compose
- For non-sudo Docker: add your user to the `docker` group, then re-login.

## Dev (hot reload)
```bash
docker compose -f docker-compose.dev.yml up --build

