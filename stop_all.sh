#!/bin/bash

# Multi-Game Platform Stop Script
# Цей скрипт зупиняє всі сервіси проекту

echo "🛑 Зупинка Multi-Game Platform..."

# Функція для зупинки процесу за PID
stop_process() {
    local pid_file=$1
    local name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🛑 Зупинка $name (PID: $pid)..."
            kill "$pid"
            rm "$pid_file"
            echo "✅ $name зупинений"
        else
            echo "❌ Процес $name вже зупинений"
            rm "$pid_file"
        fi
    else
        echo "❌ PID файл для $name не знайдений"
    fi
}

# Зупинка всіх сервісів
stop_process "logs/buckshot_api_pid.txt" "Buckshot API"
stop_process "logs/buckshot_frontend_pid.txt" "Buckshot Frontend"
stop_process "logs/blackjack_pid.txt" "Blackjack"
stop_process "logs/telegram_bot_pid.txt" "Telegram Bot"

# Додаткова зупинка за назвами процесів
echo "🔍 Пошук та зупинка залишкових процесів..."

# Зупинка Python процесів
pkill -f "buckshot_api.py" 2>/dev/null && echo "✅ Buckshot API зупинений"
pkill -f "app.py" 2>/dev/null && echo "✅ Blackjack зупинений"
pkill -f "main.py" 2>/dev/null && echo "✅ Telegram Bot зупинений"

# Зупинка Node.js процесів
pkill -f "vite" 2>/dev/null && echo "✅ Vite dev server зупинений"

echo ""
echo "🎉 Всі сервіси зупинені!"
echo "📋 Логи зберігаються в папці logs/" 