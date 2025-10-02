#!/bin/bash
# Script để rebuild và khởi động lại Onyx services
# Usage: ./rebuild_and_start.sh

set -e

# Export Docker path
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

cd "$(dirname "$0")"

echo "========================================="
echo "Onyx Rebuild & Start Script"
echo "========================================="

# Stop và xóa containers
echo ""
echo "→ Stopping và removing containers..."
docker compose down

# Rebuild backend images
echo ""
echo "→ Rebuilding backend images (api_server, background)..."
docker compose build api_server background

# Khởi động lại tất cả services với dev config
echo ""
echo "→ Starting all services with dev configuration..."
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Đợi services khởi động
echo ""
echo "→ Waiting for services to start (120 seconds)..."
sleep 120

# Kiểm tra health
echo ""
echo "→ Checking API server health..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ API Server is healthy!"
else
    echo "✗ API Server is not responding yet. Check logs with:"
    echo "  docker logs onyx-api_server-1"
fi

echo ""
echo "→ Checking services status..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep onyx

echo ""
echo "========================================="
echo "Rebuild complete!"
echo "========================================="
echo ""
echo "Test agent endpoint with:"
echo "  curl -X POST http://localhost:8080/agenthub/run \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"agent_key\": \"travel_planning_agent\", \"query\": \"Test\", \"context\": {}}'"
echo ""
echo "View logs with:"
echo "  docker logs -f onyx-api_server-1"
echo ""
