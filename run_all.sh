#!/bin/bash

# Real Estate Agent - MCP Servers Manager
# This script manages STDIO-based MCP servers

set -e  # Exit on any error

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

# Function to start an MCP server in a new terminal window
start_server_start() {
    local name=$1
    local module_path=$2
    
    print_status "Starting $name MCP server in new terminal..."
    
    # Check if we're on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use osascript to open new terminal
        osascript -e "
        tell application \"Terminal\"
            do script \"cd '$SCRIPT_DIR' && source .venv/bin/activate && python3 -m $module_path\"
            set custom title of front window to \"$name MCP Server\"
        end tell
        "
        print_success "$name MCP server started in new terminal window"
        return 0
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - try to use gnome-terminal or xterm
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal --title="$name MCP Server" -- bash -c "cd '$SCRIPT_DIR' && source .venv/bin/activate && python3 -m $module_path; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -title "$name MCP Server" -e "cd '$SCRIPT_DIR' && source .venv/bin/activate && python3 -m $module_path; bash" &
        else
            print_error "No supported terminal emulator found. Please install gnome-terminal or xterm."
            return 1
        fi
        print_success "$name MCP server started in new terminal window"
        return 0
    else
        print_error "Unsupported operating system: $OSTYPE"
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
                ((servers_stopped++))
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
        
        ((total_count++))
        
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
                
                ((running_count++))
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
    echo "  ./run_all.sh start    - Start servers in separate terminal windows"
    echo "  ./run_all.sh stop        - Stop all running servers"
    echo "  ./run_all.sh status      - Show server status"
    echo "  ./run_all.sh info        - Show this information"
}

# Function to start all servers in terminal mode
start_all_start() {
    print_status "Starting MCP servers in start windows..."
    
    # Start each server in a new terminal
    start_server_start "GIS" "gis.mcp.server"
    start_server_start "Yad2" "yad2.mcp.server"
    start_server_start "Government" "gov.mcp.server"
    
    print_success "All MCP servers started in terminal windows!"
    print_status "Each server is running in its own terminal window"
}


# Main execution
main() {
    # Get the project root directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ -d ".venv" ]; then
        print_status "Virtual environment found: .venv"
    else
        print_warning "No virtual environment found. Consider creating one."
    fi
    
    show_server_info
}

# Handle command line arguments
case "${1:-}" in
    "start")
        start_all_start
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
        echo "  start   - Start servers in separate terminal windows (recommended)"
        echo "  stop       - Stop all MCP servers"
        echo "  status     - Show status of all MCP servers"
        echo "  info       - Show server information (default)"
        exit 1
        ;;
esac
