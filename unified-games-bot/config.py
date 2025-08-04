import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in environment variables")

# Webhook Configuration
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')
WEBAPP_HOST = os.getenv('WEBAPP_HOST', 'localhost')
WEBAPP_PORT = int(os.getenv('WEBAPP_PORT', 8080))

# BlackJack Configuration
BLACKJACK_WEBAPP_URL = os.getenv('BLACKJACK_WEBAPP_URL', 'https://35233836d1c6.ngrok-free.app')
BLACKJACK_FLASK_API_URL = os.getenv('BLACKJACK_FLASK_API_URL', 'http://localhost:5000')

# Buckshot Roulette Configuration
BUCKSHOT_WEBAPP_URL = os.getenv('BUCKSHOT_WEBAPP_URL', 'https://krok1buckshot.loca.lt')
BUCKSHOT_API_URL = os.getenv('BUCKSHOT_API_URL', 'http://localhost:5001')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///unified_games.db') 