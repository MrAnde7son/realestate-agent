#!/bin/bash

# Health check script for Real Estate Agent MCP servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        print_success "$service_name is running on port $port"
        return 0
    else
        print_error "$service_name is not accessible on port $port"
        return 1
    fi
}

# Check if a port is in use
check_port() {
    local port=$1
    if lsof -i ":$port" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Main health check
main() {
    print_status "Checking Real Estate Agent services health..."
    echo ""
    
    local all_healthy=true
    
    # Check MCP servers
    print_status "Checking MCP Servers:"
    
    # Yad2 MCP Server
    if check_port 8001; then
        check_service "Yad2 MCP Server" 8001 "http://localhost:8001" || all_healthy=false
    else
        print_warning "Port 8001 is not in use - Yad2 MCP Server may not be running"
        all_healthy=false
    fi
    
    # RAMI MCP Server
    if check_port 8002; then
        check_service "RAMI MCP Server" 8002 "http://localhost:8002" || all_healthy=false
    else
        print_warning "Port 8002 is not in use - RAMI MCP Server may not be running"
        all_healthy=false
    fi
    
    # GIS MCP Server
    if check_port 8003; then
        check_service "GIS MCP Server" 8003 "http://localhost:8003" || all_healthy=false
    else
        print_warning "Port 8003 is not in use - GIS MCP Server may not be running"
        all_healthy=false
    fi
    
    # Government Data MCP Server
    if check_port 8004; then
        check_service "Government Data MCP Server" 8004 "http://localhost:8004" || all_healthy=false
    else
        print_warning "Port 8004 is not in use - Government Data MCP Server may not be running"
        all_healthy=false
    fi
    
    echo ""
    
    # Check other services
    print_status "Checking Other Services:"
    
    # Django Backend
    if check_port 8000; then
        check_service "Django Backend" 8000 "http://localhost:8000" || all_healthy=false
    else
        print_warning "Port 8000 is not in use - Django Backend may not be running"
        all_healthy=false
    fi
    
    # Frontend
    if check_port 3000; then
        check_service "Frontend" 3000 "http://localhost:3000" || all_healthy=false
    else
        print_warning "Port 3000 is not in use - Frontend may not be running"
        all_healthy=false
    fi
    
    # Redis
    if check_port 6379; then
        print_success "Redis is running on port 6379"
    else
        print_warning "Port 6379 is not in use - Redis may not be running"
        all_healthy=false
    fi
    
    # PostgreSQL
    if check_port 5432; then
        print_success "PostgreSQL is running on port 5432"
    else
        print_warning "Port 5432 is not in use - PostgreSQL may not be running"
        all_healthy=false
    fi
    
    echo ""
    
    # Summary
    if [ "$all_healthy" = true ]; then
        print_success "All services are healthy! 🎉"
        echo ""
        print_status "Services available at:"
        echo "  🌐 Frontend: http://localhost:3000"
        echo "  🔧 Django API: http://localhost:8000"
        echo "  🏠 Yad2 MCP: http://localhost:8001"
        echo "  🏛️ RAMI MCP: http://localhost:8002"
        echo "  🗺️ GIS MCP: http://localhost:8003"
        echo "  📊 Gov MCP: http://localhost:8004"
    else
        print_error "Some services are not healthy. Check the logs above."
        echo ""
        print_status "To start services, use:"
        echo "  ./docker-start.sh start-all      # Start everything"
        echo "  ./docker-start.sh start-mcp      # Start only MCP servers"
        echo "  ./docker-start.sh start-backend  # Start backend services"
        echo "  ./docker-start.sh start-frontend # Start frontend"
    fi
}

# Run health check
main "$@"
