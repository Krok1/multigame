import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import config
from handlers import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot with webhook"""
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    # Set webhook
    if config.WEBHOOK_URL:
        await bot.set_webhook(
            url=config.WEBHOOK_URL + config.WEBHOOK_PATH,
            drop_pending_updates=True
        )
        logger.info(f"Webhook set to {config.WEBHOOK_URL + config.WEBHOOK_PATH}")
    
    # Set bot commands
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="🎮 Головне меню"),
        BotCommand(command="help", description="ℹ️ Довідка"),
        BotCommand(command="rules", description="📖 Правила ігор"),
    ]
    await bot.set_my_commands(commands)
    
    # Create aiohttp application
    app = web.Application()
    
    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_handler.register(app, path=config.WEBHOOK_PATH)
    
    # Setup application
    setup_application(app, dp, bot=bot)
    
    logger.info("Starting Unified Games Bot with webhook...")
    logger.info(f"Webhook path: {config.WEBHOOK_PATH}")
    logger.info(f"Available games: Buckshot Roulette, BlackJack")
    
    # Start webhook
    web.run_app(
        app,
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}") 