# src/bot/main.py
import logging
import os

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

from src.core.database import init_database
from src.core.schema_loader import load_and_sync
from src.bot.handlers import BotHandlers
from src.services.scheduler import SchedulerService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    s3_bucket = os.environ["S3_BUCKET"]
    db_path = os.environ.get("DB_PATH", "/var/app/termin.db")

    db = init_database(f"sqlite:///{db_path}")
    db.create_tables()
    db.apply_migrations()

    logger.info("Syncing service menu from S3...")
    try:
        count = load_and_sync(db, s3_bucket)
        logger.info("Loaded %d services from S3", count)
    except Exception as e:
        logger.warning("Could not load S3 schema: %s — using existing DB data", e)

    handlers = BotHandlers(db)
    scheduler = SchedulerService(db, bot_token)

    async def post_init(application: Application) -> None:
        scheduler.start()
        logger.info("Scheduler started")

    async def post_stop(application: Application) -> None:
        scheduler.stop()

    app = (
        Application.builder()
        .token(bot_token)
        .post_init(post_init)
        .post_stop(post_stop)
        .build()
    )

    app.add_handler(CommandHandler("start", handlers.start_command))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(CommandHandler("subscribe", handlers.subscribe_command))
    app.add_handler(CommandHandler("list", handlers.list_command))
    app.add_handler(CommandHandler("unsubscribe", handlers.unsubscribe_command))
    app.add_handler(CommandHandler("check", handlers.check_command))
    app.add_handler(CommandHandler("premium", handlers.premium_command))
    app.add_handler(CommandHandler("setschedule", handlers.setschedule_command))
    app.add_handler(CommandHandler("admin", handlers.admin_command))
    app.add_handler(PreCheckoutQueryHandler(handlers.precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handlers.successful_payment_callback))
    app.add_handler(CallbackQueryHandler(handlers.button_callback))

    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
