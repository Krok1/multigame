#!/bin/bash

# Unified Games Bot Startup Script

echo "🎮 Starting Unified Games Bot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy env.example to .env and configure it:"
    echo "   cp env.example .env"
    echo "   # Then edit .env with your settings"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "🐳 Running in Docker container..."
    python run_webhook.py
else
    # Ask user for mode
    echo "🤔 Choose run mode:"
    echo "1) Polling mode (development)"
    echo "2) Webhook mode (production)"
    read -p "Enter choice (1 or 2): " choice
    
    case $choice in
        1)
            echo "🚀 Starting in polling mode..."
            python main.py
            ;;
        2)
            echo "🚀 Starting in webhook mode..."
            python run_webhook.py
            ;;
        *)
            echo "❌ Invalid choice. Starting in polling mode..."
            python main.py
            ;;
    esac
fi 