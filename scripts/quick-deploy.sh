#!/bin/bash
# Quick deploy script for UI/API changes without full rebuild
# Usage: ./scripts/quick-deploy.sh [ui|api|both]

set -e

PI_HOST="${PI_HOST:-pi@192.168.1.194}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

deploy_ui() {
    echo "Building UI..."
    cd "$PROJECT_DIR/ui"
    npm run build

    echo "Deploying UI to Pi..."
    rsync -avz --delete dist/ "$PI_HOST:/tmp/ui-dist/"
    ssh "$PI_HOST" 'docker cp /tmp/ui-dist/. $(docker ps -qf "name=ui"):/usr/share/nginx/html/ && rm -rf /tmp/ui-dist'
    echo "UI deployed!"
}

deploy_api() {
    echo "Syncing API code to Pi..."
    rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
        "$PROJECT_DIR/api/" "$PROJECT_DIR/pi_native/" \
        "$PI_HOST:/tmp/api-code/"

    echo "Restarting API container..."
    ssh "$PI_HOST" 'docker compose -f /path/to/docker-compose.pi-native.yml restart api'
    echo "API deployed!"
}

case "${1:-both}" in
    ui)
        deploy_ui
        ;;
    api)
        deploy_api
        ;;
    both)
        deploy_ui
        deploy_api
        ;;
    *)
        echo "Usage: $0 [ui|api|both]"
        exit 1
        ;;
esac
