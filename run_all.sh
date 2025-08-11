#!/bin/bash

# Real Estate Agent - MCP Servers Manager
# This script manages STDIO-based MCP servers

set -e  # Exit on any error

# Get the project root directory and Python interpreter
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer virtualenv Python if available
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON_CMD="$(command -v python3 || command -v python)"
fi

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

# Function to start an MCP server in the background
start_server() {
    local name=$1
    local module_path=$2
    local pid_file="/tmp/${name}_mcp_server.pid"
    local log_file="/tmp/${name}_mcp_output.log"

    # If server already running, skip
    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        print_warning "$name server already running (PID: $(cat "$pid_file"))"
        return 0
    fi

    print_status "Starting $name MCP server..."

    # Start server in background and record PID
    (cd "$SCRIPT_DIR" && nohup "$PYTHON_CMD" -m $module_path > "$log_file" 2>&1 & echo $! > "$pid_file")

    # Give the process a moment to start
    sleep 1

    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        print_success "$name MCP server started (PID: $(cat "$pid_file"))"
        print_status "Output: $log_file"
    else
        print_error "Failed to start $name MCP server"
        if [ -s "$log_file" ]; then
            print_status "Last log lines:"
            tail -n 20 "$log_file" | sed 's/^/    /'
        else
            print_warning "No log output captured"
        fi
        rm -f "$pid_file"
        return 1
    fi
}

# Function to stop all servers
stop_servers() {
    print_status "Stopping all MCP servers..."
    
    local servers_stopped=0
    
    # Stop servers by PID files
    for pid_file in /tmp/*_mcp_server.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            local name=$(basename "$pid_file" _mcp_server.pid)
            
            if kill -0 $pid 2>/dev/null; then
                print_status "Stopping $name server (PID: $pid)..."
                kill $pid
                sleep 1
                
                # Force kill if still running
                if kill -0 $pid 2>/dev/null; then
                    print_warning "Force killing $name server..."
                    kill -9 $pid
                fi
                
                rm "$pid_file"
                print_success "$name server stopped"
                servers_stopped=$((servers_stopped + 1))
            else
                print_warning "$name server PID file found but process not running"
                rm "$pid_file"
            fi
        fi
    done
    
    if [ $servers_stopped -eq 0 ]; then
        print_status "No running servers found"
    else
        print_success "All MCP servers stopped"
    fi
}

# Function to show server status
show_status() {
    print_status "MCP Server Status:"
    echo "=================="
    
    local running_count=0
    local total_count=0
    
    # Check each server
    for server_info in "GIS:gis.mcp.server" "Yad2:yad2.mcp.server" "Government:gov.mcp.server"; do
        local name="${server_info%:*}"
        local module="${server_info#*:}"
        local pid_file="/tmp/${name}_mcp_server.pid"
        
        total_count=$((total_count + 1))
        
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            
            if kill -0 $pid 2>/dev/null; then
                print_success "$name: Running (PID: $pid)"
                echo "  Module: $module"
                
                # Show output log if available
                local log_file="/tmp/${name}_mcp_output.log"
                if [ -f "$log_file" ]; then
                    echo "  Output log: $log_file"
                fi
                
                running_count=$((running_count + 1))
            else
                print_warning "$name: PID file exists but process not running"
                rm "$pid_file"
            fi
        else
            print_warning "$name: Not running"
            echo "  Module: $module"
        fi
        echo
    done
    
    echo "Summary: $running_count/$total_count servers running"
}

# Function to show server information
show_server_info() {
    print_status "Real Estate Agent MCP Servers Information"
    echo "=============================================="
    echo
    print_status "Available MCP Servers:"
    echo "---------------------------"
    echo "1. GIS Server (TelAvivGIS)"
    echo "   - Module: gis.mcp.server"
    echo "   - Transport: STDIO"
    echo "   - Purpose: Tel Aviv GIS data (addresses, permits, land use, etc.)"
    echo
    echo "2. Yad2 Server (Yad2RealEstate)"
    echo "   - Module: yad2.mcp.server"
    echo "   - Transport: STDIO"
    echo "   - Purpose: Yad2 real estate listings and data"
    echo
    echo "3. Government Server (DataGovIL)"
    echo "   - Module: gov.mcp.server"
    echo "   - Transport: STDIO"
    echo "   - Purpose: Israeli government data and statistics"
    echo
    print_status "Usage:"
    echo "------"
    echo "  ./run_all.sh start    - Start servers in the background"
    echo "  ./run_all.sh stop        - Stop all running servers"
    echo "  ./run_all.sh status      - Show server status"
    echo "  ./run_all.sh info        - Show this information"
}

# Function to start all servers
start_all() {
    print_status "Starting MCP servers..."

    local failures=0

    start_server "GIS" "gis.mcp.server" || failures=$((failures + 1))
    start_server "Yad2" "yad2.mcp.server" || failures=$((failures + 1))
    start_server "Government" "gov.mcp.server" || failures=$((failures + 1))

    if [ $failures -eq 0 ]; then
        print_success "All start commands issued. Use './run_all.sh status' to verify."
    else
        print_warning "$failures server(s) failed to start. Check logs above."
    fi
}


# Main execution
main() {
    cd "$SCRIPT_DIR"
    
    # Show which Python interpreter will be used
    if [ -x "$PYTHON_CMD" ]; then
        print_status "Using Python: $PYTHON_CMD"
    else
        print_error "Python interpreter not found"
        exit 1
    fi
    # Warn if virtual environment missing
    if [ ! -d ".venv" ]; then
        print_warning "No virtual environment found. Consider creating one."
    fi
    
    show_server_info
}

# Handle command line arguments
case "${1:-}" in
    "start")
        start_all
        ;;
    "stop")
        stop_servers
        ;;
    "status")
        show_status
        ;;
    "info")
        main
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [start|stop|status|info]"
        echo "  start   - Start servers in the background"
        echo "  stop       - Stop all MCP servers"
        echo "  status     - Show status of all MCP servers"
        echo "  info       - Show server information (default)"
        exit 1
        ;;
esac
