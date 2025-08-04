#!/bin/bash

# 🎮 Unified Games Bot - Start All Services Script

echo "🎮 Starting Unified Games Bot Services..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $1 is already in use!${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $1 is available${NC}"
        return 0
    fi
}

# Function to start service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    
    echo -e "${BLUE}🚀 Starting $name on port $port...${NC}"
    
    # Check if port is available
    if ! check_port $port; then
        echo -e "${RED}❌ Cannot start $name - port $port is busy${NC}"
        return 1
    fi
    
    # Start service in background
    eval "$command" > logs/${name}.log 2>&1 &
    local pid=$!
    echo $pid > pids/${name}.pid
    
    # Wait a bit for service to start
    sleep 3
    
    # Check if service is running
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $name started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start $name${NC}"
        return 1
    fi
}

# Create necessary directories
mkdir -p logs pids

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📁 Working directory: $SCRIPT_DIR${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "📝 Please copy env.example to .env and configure it:"
    echo "   cp env.example .env"
    exit 1
fi

# Load environment variables
source .env

echo -e "${BLUE}🔧 Configuration loaded:${NC}"
echo "   BOT_TOKEN: ${BOT_TOKEN:0:10}..."
echo "   BLACKJACK_FLASK_API_URL: $BLACKJACK_FLASK_API_URL"
echo "   BLACKJACK_WEBAPP_URL: $BLACKJACK_WEBAPP_URL"
echo "   BUCKSHOT_WEBAPP_URL: $BUCKSHOT_WEBAPP_URL"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install -r requirements.txt > logs/install.log 2>&1

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"

# 1. Start BlackJack Flask API (port 5000)
cd ../cards-main
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
start_service "blackjack-api" "python app.py" 5000
cd "$SCRIPT_DIR"

# 2. Start Buckshot Roulette React App (port 3000)
cd ../buckshot-roulette
if [ -f "node_modules/.bin/vite" ]; then
    start_service "buckshot-webapp" "npm run dev" 3000
else
    echo -e "${YELLOW}⚠️  Buckshot Roulette not installed. Run 'npm install' first.${NC}"
fi
cd "$SCRIPT_DIR"

# 3. Start Unified Bot (port 8080)
start_service "unified-bot" "python run_webhook.py" 8080

# Wait a moment for all services to start
sleep 5

echo -e "${GREEN}🎉 All services started!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo "   BlackJack API: http://localhost:5000"
echo "   Buckshot Roulette: http://localhost:3000"
echo "   Unified Bot: http://localhost:8080"
echo ""
echo -e "${YELLOW}🌐 Next steps:${NC}"
echo "1. Start ngrok tunnels:"
echo "   ngrok http 5000  # For BlackJack API"
echo "   ngrok http 3000  # For Buckshot Roulette"
echo ""
echo "2. Update .env with ngrok URLs"
echo "3. Test the bot in Telegram"
echo ""
echo -e "${BLUE}📝 Logs are available in the 'logs' directory${NC}"
echo -e "${BLUE}🛑 To stop all services: ./stop_all_services.sh${NC}" 