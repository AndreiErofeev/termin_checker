"""
Telegram Bot Main Entry Point

Starts the bot and registers handlers.
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

from src.core.database import init_database
from src.bot.handlers import BotHandlers

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    # Get bot token
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return

    # Initialize database
    logger.info("Initializing database...")
    db = init_database()

    # Initialize handlers
    logger.info("Initializing bot handlers...")
    handlers = BotHandlers(db)

    # Create application
    logger.info("Creating bot application...")
    application = Application.builder().token(bot_token).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("subscribe", handlers.subscribe_command))
    application.add_handler(CommandHandler("list", handlers.list_command))
    application.add_handler(CommandHandler("unsubscribe", handlers.unsubscribe_command))
    application.add_handler(CommandHandler("check", handlers.check_command))

    # Register callback query handler for buttons
    application.add_handler(CallbackQueryHandler(handlers.button_callback))

    # Start bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == '__main__':
    main()
