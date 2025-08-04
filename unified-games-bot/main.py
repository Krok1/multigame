import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from handlers import router
from models import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the unified games bot"""
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    # Delete webhook if it exists (for polling mode)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted successfully")
    except Exception as e:
        logger.warning(f"Failed to delete webhook: {e}")
    
    # Set bot commands (Ukrainian by default)
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="🎮 Головне меню"),
        BotCommand(command="help", description="ℹ️ Довідка"),
        BotCommand(command="rules", description="📖 Правила ігор"),
        BotCommand(command="join", description="👥 Приєднатися до гри"),
    ]
    await bot.set_my_commands(commands)
    
    logger.info("Starting Unified Games Bot...")
    logger.info("Available games: Buckshot Roulette, BlackJack")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}") 