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

async def on_startup(bot: Bot) -> None:
    """Set webhook on startup"""
    webhook_url = f"{config.WEBHOOK_URL}{config.WEBHOOK_PATH}"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

async def on_shutdown(bot: Bot) -> None:
    """Delete webhook on shutdown"""
    await bot.delete_webhook()
    logger.info("Webhook deleted")

def create_app() -> web.Application:
    """Create aiohttp application"""
    # Initialize bot and dispatcher
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    # Set startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Create aiohttp application
    app = web.Application()
    
    # Create webhook request handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    # Register webhook handler
    webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
    
    # Setup application
    setup_application(app, dp, bot=bot)
    
    return app

async def main():
    """Main function to run webhook server"""
    app = create_app()
    
    # Create and start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, config.WEBAPP_HOST, config.WEBAPP_PORT)
    await site.start()
    
    logger.info(f"Webhook server started on {config.WEBAPP_HOST}:{config.WEBAPP_PORT}")
    
    try:
        # Keep server running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")