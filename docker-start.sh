#!/bin/bash

# Real Estate Agent Docker Startup Script
# This script provides easy management of all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop or Docker daemon."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Function to get docker-compose command
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo "docker compose"
    fi
}

# Function to start all services
start_all() {
    print_status "Starting all services..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    
    # Build and start all services
    $DOCKER_COMPOSE up --build -d
    
    print_success "All services started!"
    print_status "Services will be available at:"
    echo "  🌐 Frontend: http://localhost:3000"
    echo "  🔧 Django API: http://localhost:8000"
    echo "  🏠 Yad2 MCP: http://localhost:8001"
    echo "  🏛️ RAMI MCP: http://localhost:8002"
    echo "  🗺️ GIS MCP: http://localhost:8003"
    echo "  📊 Gov MCP: http://localhost:8004"
    echo "  🗄️ PostgreSQL: localhost:5432"
    echo "  🔴 Redis: localhost:6379"
}

# Function to start only MCP servers
start_mcp_only() {
    print_status "Starting MCP servers only..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    
    # Start only MCP services
    $DOCKER_COMPOSE up --build -d yad2-mcp rami-mcp gis-mcp gov-mcp
    
    print_success "MCP servers started!"
    print_status "MCP services available at:"
    echo "  🏠 Yad2 MCP: http://localhost:8001"
    echo "  🏛️ RAMI MCP: http://localhost:8002"
    echo "  🗺️ GIS MCP: http://localhost:8003"
    echo "  📊 Gov MCP: http://localhost:8004"
}

# Function to start backend services
start_backend() {
    print_status "Starting backend services..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    
    # Start backend services
    $DOCKER_COMPOSE up --build -d redis postgres django celery-worker celery-beat
    
    print_success "Backend services started!"
    print_status "Backend services available at:"
    echo "  🔧 Django API: http://localhost:8000"
    echo "  🗄️ PostgreSQL: localhost:5432"
    echo "  🔴 Redis: localhost:6379"
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    
    # Start frontend
    $DOCKER_COMPOSE up --build -d frontend
    
    print_success "Frontend started!"
    print_status "Frontend available at: http://localhost:3000"
}

# Function to stop all services
stop_all() {
    print_status "Stopping all services..."
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE down
    print_success "All services stopped"
}

# Function to show service status
show_status() {
    print_status "Service status:"
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    $DOCKER_COMPOSE ps
}

# Function to show logs
show_logs() {
    local service=${1:-""}
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    
    if [ -z "$service" ]; then
        print_status "Showing logs for all services (Ctrl+C to exit)..."
        $DOCKER_COMPOSE logs -f
    else
        print_status "Showing logs for $service (Ctrl+C to exit)..."
        $DOCKER_COMPOSE logs -f "$service"
    fi
}

# Function to rebuild services
rebuild() {
    local service=${1:-""}
    DOCKER_COMPOSE=$(get_docker_compose_cmd)
    
    if [ -z "$service" ]; then
        print_status "Rebuilding all services..."
        $DOCKER_COMPOSE down
        $DOCKER_COMPOSE build --no-cache
        $DOCKER_COMPOSE up -d
        print_success "All services rebuilt and started"
    else
        print_status "Rebuilding $service..."
        $DOCKER_COMPOSE stop "$service"
        $DOCKER_COMPOSE build --no-cache "$service"
        $DOCKER_COMPOSE up -d "$service"
        print_success "$service rebuilt and started"
    fi
}

# Function to clean up
cleanup() {
    print_warning "This will remove all containers, volumes, and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up Docker environment..."
        DOCKER_COMPOSE=$(get_docker_compose_cmd)
        $DOCKER_COMPOSE down -v --rmi all
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to show help
show_help() {
    echo "Real Estate Agent Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start-all      Start all services (frontend, backend, MCP servers)"
    echo "  start-mcp      Start only MCP servers for data access"
    echo "  start-backend  Start backend services (Django, Redis, PostgreSQL)"
    echo "  start-frontend Start frontend (Next.js)"
    echo "  stop           Stop all services"
    echo "  status         Show service status"
    echo "  logs [SERVICE] Show logs (all services or specific service)"
    echo "  rebuild [SERVICE] Rebuild services (all or specific)"
    echo "  cleanup        Remove all containers, volumes, and images"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start-all           # Start everything"
    echo "  $0 start-mcp           # Start only MCP servers for data"
    echo "  $0 logs yad2-mcp       # Show Yad2 MCP server logs"
    echo "  $0 rebuild frontend    # Rebuild frontend service"
    echo ""
    echo "Service Ports:"
    echo "  Frontend: 3000, Django: 8000, Yad2: 8001, RAMI: 8002, GIS: 8003, Gov: 8004"
}

# Main script logic
main() {
    # Check prerequisites
    check_docker
    check_docker_compose
    
    case "${1:-help}" in
        "start-all")
            start_all
            ;;
        "start-mcp")
            start_mcp_only
            ;;
        "start-backend")
            start_backend
            ;;
        "start-frontend")
            start_frontend
            ;;
        "stop")
            stop_all
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "rebuild")
            rebuild "$2"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
