#!/usr/bin/env python3
"""
Main entry point for the Telegram Meme Classifier Bot
"""

import logging
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from bot.config import BotConfig
from bot.handlers import MemeBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Main function to start the bot"""
    try:
        # Initialize bot
        bot = MemeBot()
        
        # Build application
        application = ApplicationBuilder().token(BotConfig.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
        application.add_handler(MessageHandler(filters.ALL & ~filters.PHOTO, bot.start))
        application.add_handler(CallbackQueryHandler(bot.handle_approval, pattern="^approve_"))
        application.add_handler(CallbackQueryHandler(bot.handle_temperature, pattern="^temp_"))
        
        # Start bot
        logger.info("Starting Telegram Meme Classifier Bot...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
