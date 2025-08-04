#!/bin/bash

# 🎮 Unified Games Bot - Stop All Services Script

echo "🛑 Stopping Unified Games Bot Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to stop service by PID
stop_service() {
    local name=$1
    local pid_file="pids/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo -e "${BLUE}🛑 Stopping $name (PID: $pid)...${NC}"
        
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 2
            
            # Check if process is still running
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force killing $name...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name was not running${NC}"
        fi
        
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $name${NC}"
    fi
}

# Stop all services
echo -e "${YELLOW}🛑 Stopping services...${NC}"

stop_service "unified-bot"
stop_service "blackjack-api"
stop_service "buckshot-webapp"

# Kill any remaining processes on our ports
echo -e "${BLUE}🧹 Cleaning up ports...${NC}"

for port in 5000 3000 8080; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}⚠️  Killing process on port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null
    fi
done

echo -e "${GREEN}🎉 All services stopped!${NC}"
echo ""
echo -e "${BLUE}📝 Logs are still available in the 'logs' directory${NC}"
echo -e "${BLUE}🚀 To restart: ./start_all_services.sh${NC}" 