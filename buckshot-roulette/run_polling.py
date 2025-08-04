#!/usr/bin/env python3
"""
Script to run the bot in polling mode (for development)
"""
import asyncio
import logging
from main import main

# Configure logging for the runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🎯 Starting Buckshot Roulette Bot in polling mode...")
    logger.info("Press Ctrl+C to stop")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")