#!/usr/bin/env python3
"""
Script to run the bot in webhook mode (for production)
"""
import asyncio
from webhook_server import main

if __name__ == "__main__":
    print("🎯 Starting Buckshot Roulette Bot webhook server...")
    print("Press Ctrl+C to stop")
    asyncio.run(main())