# EggBot - Pi-Native BBQ Controller

Raspberry Pi-based controller for Big Green Egg style BBQ grills with direct hardware control.
Features automated temperature control, multi-probe monitoring, and web-based interface.

## Prereqs
- Docker and Docker Compose
- For non-sudo Docker: add your user to the `docker` group, then re-login.

## Dev (hot reload)
```bash
docker compose -f docker-compose.dev.yml up --build

