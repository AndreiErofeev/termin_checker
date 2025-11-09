"""
Telegram Bot Command Handlers

Handles all bot commands and user interactions.
"""

import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..core.database import Database
from ..services import UserService, SubscriptionService, CheckService
from ..core.models import Service

logger = logging.getLogger(__name__)


class BotHandlers:
    """Handler class for bot commands"""

    def __init__(self, db: Database):
        """
        Initialize bot handlers

        Args:
            db: Database instance
        """
        self.db = db
        self.user_service = UserService(db)
        self.subscription_service = SubscriptionService(db)
        self.check_service = CheckService(db)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user

        # Create or update user in database
        db_user = self.user_service.create_or_update_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        welcome_message = (
            f"👋 Welcome {user.first_name}!\n\n"
            "This bot helps you monitor appointment availability "
            "for Düsseldorf city services.\n\n"
            "Available commands:\n"
            "/subscribe - Subscribe to a service\n"
            "/list - View your subscriptions\n"
            "/unsubscribe - Cancel a subscription\n"
            "/check - Run manual check\n"
            "/help - Show help message\n\n"
            f"Your plan: {db_user.plan.value.upper()}"
        )

        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📖 *Help & Commands*\n\n"
            "*Available Commands:*\n"
            "/start - Start the bot\n"
            "/subscribe - Subscribe to appointment notifications\n"
            "/list - View your active subscriptions\n"
            "/unsubscribe - Cancel a subscription\n"
            "/check - Manually check for appointments\n"
            "/help - Show this help message\n\n"
            "*How it works:*\n"
            "1. Subscribe to a service using /subscribe\n"
            "2. The bot will check for appointments automatically\n"
            "3. You'll receive a notification when appointments are found\n"
            "4. Manage your subscriptions with /list and /unsubscribe\n\n"
            "*Subscription Plans:*\n"
            "• FREE: Up to 3 subscriptions, checks every 2 hours\n"
            "• PREMIUM: Unlimited subscriptions, checks every 15 minutes"
        )

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command - show user's subscriptions"""
        user = update.effective_user

        # Get user from database
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        # Get subscriptions
        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)

        if not subscriptions:
            await update.message.reply_text(
                "📭 You have no active subscriptions.\n\n"
                "Use /subscribe to start monitoring a service."
            )
            return

        # Format subscription list
        message = "📋 *Your Active Subscriptions:*\n\n"

        for idx, sub in enumerate(subscriptions, 1):
            service = sub.service
            last_check = sub.last_checked.strftime("%Y-%m-%d %H:%M") if sub.last_checked else "Never"

            message += (
                f"{idx}. *{service.service_name}*\n"
                f"   Category: {service.category}\n"
                f"   Check interval: Every {sub.interval_hours}h\n"
                f"   Last checked: {last_check}\n"
                f"   ID: `{sub.id}`\n\n"
            )

        message += f"\nTotal: {len(subscriptions)} subscription(s)"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command - start subscription flow"""
        user = update.effective_user

        # Get user from database
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        # Get available services
        with self.db.get_session() as session:
            services = session.query(Service).filter(Service.active == True).all()

            if not services:
                await update.message.reply_text("❌ No services available at the moment.")
                return

            # Group services by category
            categories = {}
            for service in services:
                if service.category not in categories:
                    categories[service.category] = []
                categories[service.category].append(service)

            # Create inline keyboard with categories
            keyboard = []
            for category in sorted(categories.keys()):
                service_count = len(categories[category])
                keyboard.append([
                    InlineKeyboardButton(
                        f"{category} ({service_count})",
                        callback_data=f"cat_{category[:50]}"
                    )
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "📝 *Select a category:*\n\n"
                "Choose a service category to subscribe to:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unsubscribe command"""
        user = update.effective_user

        # Get user from database
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        # Get subscriptions
        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)

        if not subscriptions:
            await update.message.reply_text("📭 You have no active subscriptions.")
            return

        # Create inline keyboard with subscriptions
        keyboard = []
        for sub in subscriptions:
            service = sub.service
            keyboard.append([
                InlineKeyboardButton(
                    f"{service.service_name[:40]}...",
                    callback_data=f"unsub_{sub.id}"
                )
            ])

        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🗑️ *Select subscription to cancel:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /check command - manually trigger check"""
        user = update.effective_user

        # Get user from database
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        # Get subscriptions
        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)

        if not subscriptions:
            await update.message.reply_text(
                "📭 You have no active subscriptions.\n\n"
                "Use /subscribe to start monitoring a service."
            )
            return

        # Create inline keyboard with subscriptions
        keyboard = []
        for sub in subscriptions:
            service = sub.service
            keyboard.append([
                InlineKeyboardButton(
                    f"{service.service_name[:40]}...",
                    callback_data=f"check_{sub.id}"
                )
            ])

        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔍 *Select subscription to check:*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "cancel":
            await query.edit_message_text("❌ Cancelled.")
            return

        # Handle category selection
        if data.startswith("cat_"):
            category = data[4:]
            await self._show_services_in_category(query, category)

        # Handle service selection
        elif data.startswith("srv_"):
            service_id = int(data[4:])
            await self._create_subscription(query, service_id)

        # Handle unsubscribe
        elif data.startswith("unsub_"):
            subscription_id = int(data[6:])
            await self._handle_unsubscribe(query, subscription_id)

        # Handle manual check
        elif data.startswith("check_"):
            subscription_id = int(data[6:])
            await self._handle_manual_check(query, subscription_id)

    async def _show_services_in_category(self, query, category: str):
        """Show services in selected category"""
        with self.db.get_session() as session:
            services = session.query(Service).filter(
                Service.category == category,
                Service.active == True
            ).all()

            if not services:
                await query.edit_message_text("❌ No services found in this category.")
                return

            # Create inline keyboard with services
            keyboard = []
            for service in services[:20]:  # Limit to 20 to avoid message too long
                keyboard.append([
                    InlineKeyboardButton(
                        service.service_name[:60],
                        callback_data=f"srv_{service.id}"
                    )
                ])

            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_categories")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"📝 *Select a service from {category}:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def _create_subscription(self, query, service_id: int):
        """Create subscription for user"""
        user = query.from_user

        # Get user from database
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await query.edit_message_text("❌ User not found.")
            return

        # Create subscription
        subscription = self.subscription_service.create_subscription(
            user_id=db_user.id,
            service_id=service_id,
            interval_hours=1,
            quantity=1
        )

        if subscription:
            service = subscription.service
            await query.edit_message_text(
                f"✅ *Subscription created!*\n\n"
                f"Service: {service.service_name}\n"
                f"Category: {service.category}\n"
                f"Check interval: Every {subscription.interval_hours}h\n\n"
                f"You'll receive notifications when appointments are available.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Failed to create subscription.")

    async def _handle_unsubscribe(self, query, subscription_id: int):
        """Handle unsubscribe action"""
        success = self.subscription_service.delete_subscription(subscription_id)

        if success:
            await query.edit_message_text("✅ Subscription cancelled successfully.")
        else:
            await query.edit_message_text("❌ Failed to cancel subscription.")

    async def _handle_manual_check(self, query, subscription_id: int):
        """Handle manual check action"""
        await query.edit_message_text("🔍 Checking for appointments... Please wait.")

        try:
            # Run check
            check = await self.check_service.run_subscription_check(subscription_id)

            if not check:
                await query.edit_message_text("❌ Failed to run check.")
                return

            if check.available and check.appointments:
                # Format appointment list
                message = (
                    f"✅ *Found {check.appointment_count} appointment(s)!*\n\n"
                )

                for apt in check.appointments[:10]:  # Limit to 10
                    message += f"📅 {apt.appointment_date} at {apt.appointment_time}\n"

                if check.appointment_count > 10:
                    message += f"\n... and {check.appointment_count - 10} more"

                await query.edit_message_text(message, parse_mode='Markdown')
            else:
                await query.edit_message_text(
                    "❌ No appointments available at the moment.\n\n"
                    "The bot will notify you when appointments become available."
                )

        except Exception as e:
            logger.error(f"Error in manual check: {e}", exc_info=True)
            await query.edit_message_text(f"❌ Error: {str(e)}")
