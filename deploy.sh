#!/bin/bash

# Onyx Deployment Script
# Manages Docker Compose deployment easily

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_DIR="$SCRIPT_DIR/deployment/docker_compose"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$DOCKER_COMPOSE_DIR"

function print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

function print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

function print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

function check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running!"
        exit 1
    fi
    
    print_status "Docker is running"
}

function show_status() {
    print_status "Container Status:"
    docker compose ps
    echo ""
    print_status "Memory Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

function start_services() {
    print_status "Starting Onyx services..."
    docker compose up -d --build
    echo ""
    print_status "Waiting for services to start (30 seconds)..."
    sleep 30
    
    print_status "Checking API health..."
    if curl -s http://localhost/api/health | grep -q "success"; then
        print_status "✓ API Server is healthy!"
    else
        print_warning "API Server might still be starting up..."
        print_warning "Check logs with: docker compose logs -f api_server"
    fi
    
    echo ""
    print_status "Deployment complete!"
    echo ""
    echo "Access the application at:"
    echo "  Web UI:  http://localhost:3000"
    echo "  API:     http://localhost/api"
    echo ""
    show_status
}

function stop_services() {
    print_status "Stopping Onyx services..."
    docker compose stop
    print_status "Services stopped"
}

function restart_services() {
    print_status "Restarting Onyx services..."
    docker compose restart
    print_status "Services restarted"
}

function clean_all() {
    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_status "Cleaning up..."
        docker compose down -v
        print_status "Cleanup complete"
    else
        print_status "Cleanup cancelled"
    fi
}

function show_logs() {
    service=${1:-""}
    if [ -z "$service" ]; then
        docker compose logs -f
    else
        docker compose logs -f "$service"
    fi
}

function show_help() {
    cat << EOF
Onyx Deployment Script

Usage: ./deploy.sh [command] [options]

Commands:
    start       Start all services
    stop        Stop all services (keeps data)
    restart     Restart all services
    status      Show container status and memory usage
    logs        Show logs (optionally specify service name)
    clean       Remove all containers and volumes
    help        Show this help message

Examples:
    ./deploy.sh start
    ./deploy.sh logs api_server
    ./deploy.sh status

EOF
}

# Main
check_docker

case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
