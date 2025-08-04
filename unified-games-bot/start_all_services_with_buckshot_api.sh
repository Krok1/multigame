#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎮 Запуск всіх сервісів для Unified Games Bot${NC}"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Помилка: Запустіть скрипт з директорії unified-games-bot${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Віртуальне середовище не знайдено. Створюю...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Файл .env не знайдено. Копіюю з env.example...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  Будь ласка, відредагуйте .env файл і встановіть BOT_TOKEN${NC}"
    echo -e "${YELLOW}⚠️  Потім запустіть скрипт знову${NC}"
    exit 1
fi

# Check ports availability
echo -e "${BLUE}🔍 Перевірка доступності портів...${NC}"

check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Порт $1 вже використовується${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Порт $1 доступний${NC}"
        return 0
    fi
}

check_port 5000 || exit 1
check_port 5001 || exit 1
check_port 3000 || exit 1

# Create logs directory
mkdir -p logs

# Function to start service
start_service() {
    local name=$1
    local command=$2
    local log_file=$3
    
    echo -e "${BLUE}🚀 Запуск $name...${NC}"
    $command > "logs/$log_file" 2>&1 &
    local pid=$!
    echo $pid > "logs/${name}_pid.txt"
    echo -e "${GREEN}✅ $name запущений (PID: $pid)${NC}"
    sleep 2
}

# Start BlackJack API
echo -e "${BLUE}🃏 Запуск BlackJack API...${NC}"
cd ../cards-main
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Створюю віртуальне середовище для BlackJack...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

python3 app.py > ../unified-games-bot/logs/blackjack_api.log 2>&1 &
BLACKJACK_PID=$!
echo $BLACKJACK_PID > ../unified-games-bot/logs/blackjack_api_pid.txt
echo -e "${GREEN}✅ BlackJack API запущений (PID: $BLACKJACK_PID)${NC}"
cd ../unified-games-bot

# Start Buckshot API
echo -e "${BLUE}🎰 Запуск Buckshot API...${NC}"
cd ../buckshot-roulette/python
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Створюю віртуальне середовище для Buckshot API...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

python3 buckshot_api.py > ../../unified-games-bot/logs/buckshot_api.log 2>&1 &
BUCKSHOT_API_PID=$!
echo $BUCKSHOT_API_PID > ../../unified-games-bot/logs/buckshot_api_pid.txt
echo -e "${GREEN}✅ Buckshot API запущений (PID: $BUCKSHOT_API_PID)${NC}"
cd ../../unified-games-bot

# Start Buckshot Frontend
echo -e "${BLUE}🎰 Запуск Buckshot Frontend...${NC}"
cd ../buckshot-roulette
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  Встановлюю залежності для Buckshot...${NC}"
    npm install
fi

npm run dev > ../unified-games-bot/logs/buckshot_frontend.log 2>&1 &
BUCKSHOT_FRONTEND_PID=$!
echo $BUCKSHOT_FRONTEND_PID > ../unified-games-bot/logs/buckshot_frontend_pid.txt
echo -e "${GREEN}✅ Buckshot Frontend запущений (PID: $BUCKSHOT_FRONTEND_PID)${NC}"
cd ../unified-games-bot

# Wait a bit for services to start
echo -e "${BLUE}⏳ Чекаю запуску сервісів...${NC}"
sleep 5

# Start Unified Bot
echo -e "${BLUE}🤖 Запуск Unified Games Bot...${NC}"
python3 main.py > logs/unified_bot.log 2>&1 &
UNIFIED_BOT_PID=$!
echo $UNIFIED_BOT_PID > logs/unified_bot_pid.txt
echo -e "${GREEN}✅ Unified Games Bot запущений (PID: $UNIFIED_BOT_PID)${NC}"

# Show status
echo -e "${GREEN}🎉 Всі сервіси запущені!${NC}"
echo -e "${BLUE}📊 Статус сервісів:${NC}"
echo -e "  🃏 BlackJack API: ${GREEN}✅${NC} (PID: $BLACKJACK_PID)"
echo -e "  🎰 Buckshot API: ${GREEN}✅${NC} (PID: $BUCKSHOT_API_PID)"
echo -e "  🎰 Buckshot Frontend: ${GREEN}✅${NC} (PID: $BUCKSHOT_FRONTEND_PID)"
echo -e "  🤖 Unified Bot: ${GREEN}✅${NC} (PID: $UNIFIED_BOT_PID)"

echo -e "${YELLOW}⚠️  Тепер потрібно запустити localtunnel для обох сервісів:${NC}"
echo -e "${BLUE}📡 Термінал 1 (BlackJack):${NC}"
echo -e "  npx localtunnel --port 5000 --subdomain krok1games"
echo -e "${BLUE}📡 Термінал 2 (Buckshot):${NC}"
echo -e "  npx localtunnel --port 3000 --subdomain krok1buckshot"
echo -e "${BLUE}📡 Термінал 3 (Buckshot API):${NC}"
echo -e "  npx localtunnel --port 5001 --subdomain krok1buckshotapi"

echo -e "${GREEN}🎮 Тепер можете тестувати бота!${NC}"
echo -e "${BLUE}📝 Логи зберігаються в папці logs/${NC}"

# Keep script running
echo -e "${YELLOW}💡 Натисніть Ctrl+C для зупинки всіх сервісів${NC}"
trap 'echo -e "${RED}🛑 Зупинка всіх сервісів...${NC}"; ./stop_all_services.sh; exit' INT
wait 