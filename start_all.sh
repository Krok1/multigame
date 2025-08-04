#!/bin/bash

# Multi-Game Platform Startup Script
# Цей скрипт запускає всі сервіси проекту

echo "🎮 Запуск Multi-Game Platform..."

# Функція для перевірки чи запущений процес
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo "✅ $2 вже запущений"
        return 0
    else
        echo "❌ $2 не запущений"
        return 1
    fi
}

# Функція для запуску процесу в фоновому режимі
start_background() {
    local dir=$1
    local command=$2
    local name=$3
    
    echo "🚀 Запуск $name..."
    cd "$dir" || exit 1
    
    if [[ "$command" == *"npm"* ]]; then
        # Для Node.js проектів
        if [ ! -d "node_modules" ]; then
            echo "📦 Встановлення залежностей для $name..."
            npm install
        fi
    elif [[ "$command" == *"python"* ]]; then
        # Для Python проектів
        if [ ! -d "venv" ]; then
            echo "🐍 Створення віртуального середовища для $name..."
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    nohup $command > "../logs/${name,,}.log" 2>&1 &
    echo $! > "../logs/${name,,}_pid.txt"
    echo "✅ $name запущений (PID: $!)"
    cd ..
}

# Створення папки для логів
mkdir -p logs

# 1. Запуск Buckshot Roulette Backend
if ! check_process "buckshot_api.py" "Buckshot API"; then
    start_background "buckshot-roulette" "python buckshot_api.py" "Buckshot API"
fi

# 2. Запуск Buckshot Roulette Frontend
if ! check_process "vite" "Buckshot Frontend"; then
    start_background "buckshot-roulette" "npm run dev" "Buckshot Frontend"
fi

# 3. Запуск Blackjack
if ! check_process "app.py" "Blackjack"; then
    start_background "cards-main" "python app.py" "Blackjack"
fi

# 4. Запуск Telegram Bot
if ! check_process "main.py" "Telegram Bot"; then
    start_background "unified-games-bot" "python main.py" "Telegram Bot"
fi

echo ""
echo "🎉 Всі сервіси запущені!"
echo ""
echo "📱 Доступні сервіси:"
echo "   • Buckshot Roulette: http://localhost:5173"
echo "   • Blackjack: http://localhost:5000"
echo "   • Telegram Bot: Перевірте логи в папці logs/"
echo ""
echo "📋 Логи зберігаються в папці logs/"
echo "🛑 Для зупинки всіх сервісів виконайте: ./stop_all.sh" 