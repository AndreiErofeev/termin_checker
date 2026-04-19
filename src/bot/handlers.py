"""
Telegram Bot Command Handlers

Handles all bot commands and user interactions.
"""

import logging
import os
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

from ..core.database import Database
from ..services import UserService, SubscriptionService, CheckService
from ..core.models import Service, UserPlan, User, Subscription

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
        self.admin_id = int(os.environ.get("ADMIN_TELEGRAM_ID", 0))

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
            last_check = sub.last_checked_at.strftime("%Y-%m-%d %H:%M") if sub.last_checked_at else "Never"

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

        # Get available services grouped by department
        with self.db.get_session() as session:
            services = session.query(Service).filter(Service.active == True).all()

            if not services:
                await update.message.reply_text("❌ No services available at the moment.")
                return

            depts: dict[str, int] = {}
            for service in services:
                dept = service.department or "Other"
                depts[dept] = depts.get(dept, 0) + 1

            keyboard = [
                [InlineKeyboardButton(f"{dept} ({count})", callback_data=f"dept_{dept[:55]}")]
                for dept, count in sorted(depts.items())
            ]
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

            await update.message.reply_text(
                "📝 *Select a department:*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown',
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

        if data == "back_depts":
            await self._show_departments(query)
            return

        if data == "back_categories":
            # We don't store the dept in callback state, so re-show dept list
            await self._show_departments(query)
            return

        # Handle department selection
        if data.startswith("dept_"):
            dept = data[5:]
            await self._show_categories_in_dept(query, dept)

        # Handle category selection
        elif data.startswith("cat_"):
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

    async def _show_departments(self, query):
        """Show department selection (used by subscribe and Back button)"""
        with self.db.get_session() as session:
            services = session.query(Service).filter(Service.active == True).all()

            if not services:
                await query.edit_message_text("❌ No services available at the moment.")
                return

            depts: dict[str, int] = {}
            for service in services:
                dept = service.department or "Other"
                depts[dept] = depts.get(dept, 0) + 1

            keyboard = [
                [InlineKeyboardButton(f"{dept} ({count})", callback_data=f"dept_{dept[:55]}")]
                for dept, count in sorted(depts.items())
            ]

            await query.edit_message_text(
                "📝 *Select a department:*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown',
            )

    async def _show_categories_in_dept(self, query, dept: str):
        """Show categories within a department"""
        with self.db.get_session() as session:
            services = session.query(Service).filter(
                Service.department.like(f"{dept}%"),
                Service.active == True,
            ).all()

            if not services:
                await query.edit_message_text("❌ No services found.")
                return

            cats: dict[str, int] = {}
            for service in services:
                cats[service.category] = cats.get(service.category, 0) + 1

            keyboard = [
                [InlineKeyboardButton(f"{cat} ({count})", callback_data=f"cat_{cat[:55]}")]
                for cat, count in sorted(cats.items())
            ]
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_depts")])

            await query.edit_message_text(
                f"📝 *{dept}*\n\nSelect a category:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

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
        user = query.from_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await query.edit_message_text("❌ User not found.")
            return

        is_free = db_user.plan == UserPlan.FREE

        if is_free:
            existing = self.subscription_service.get_user_subscriptions(db_user.id)
            if len(existing) >= 3:
                await query.edit_message_text(
                    "❌ Free plan allows up to 3 subscriptions.\n\n"
                    "Use /premium to upgrade and get unlimited subscriptions."
                )
                return
            interval_hours = 12
        else:
            interval_hours = 1  # premium default, can be changed with /setschedule

        subscription = self.subscription_service.create_subscription(
            user_id=db_user.id,
            service_id=service_id,
            interval_hours=interval_hours,
            quantity=1,
        )

        if subscription:
            service = subscription.service
            freq = "twice daily" if is_free else f"every {interval_hours}h"
            await query.edit_message_text(
                f"✅ *Subscribed!*\n\n"
                f"Service: {service.service_name}\n"
                f"Category: {service.category}\n"
                f"Checks: {freq}\n\n"
                f"Running first check now...",
                parse_mode="Markdown",
            )
            await self._run_check_and_reply(query, subscription.id)
        else:
            await query.edit_message_text("❌ Already subscribed to this service.")

    async def _handle_unsubscribe(self, query, subscription_id: int):
        """Handle unsubscribe action"""
        success = self.subscription_service.delete_subscription(subscription_id)

        if success:
            await query.edit_message_text("✅ Subscription cancelled successfully.")
        else:
            await query.edit_message_text("❌ Failed to cancel subscription.")

    async def _run_check_and_reply(self, query, subscription_id: int):
        try:
            check = await self.check_service.run_subscription_check(subscription_id)

            if not check:
                await query.edit_message_text("❌ Failed to run check.")
                return

            if check.available and check.appointments:
                message = f"✅ *Found {check.appointment_count} appointment(s)!*\n\n"
                for apt in check.appointments[:10]:
                    message += f"📅 {apt.appointment_date} at {apt.appointment_time}\n"
                if check.appointment_count > 10:
                    message += f"\n... and {check.appointment_count - 10} more"
                await query.edit_message_text(message, parse_mode='Markdown')
            else:
                await query.edit_message_text(
                    "❌ No appointments available right now.\n\n"
                    "The bot will notify you when slots open up."
                )

        except Exception as e:
            logger.error(f"Error in check: {e}", exc_info=True)
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def _handle_manual_check(self, query, subscription_id: int):
        await query.edit_message_text("🔍 Checking for appointments... Please wait.")
        await self._run_check_and_reply(query, subscription_id)

    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚧 Premium subscriptions are temporarily unavailable. Check back soon!")
        return

        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ Please use /start first.")
            return

        if db_user.plan != UserPlan.FREE:
            await update.message.reply_text("✅ You already have Premium!")
            return

        await context.bot.send_invoice(
            chat_id=user.id,
            title="Termin Checker Premium",
            description="Unlimited subscriptions + custom check schedule",
            payload="premium_upgrade",
            currency="XTR",
            prices=[LabeledPrice("Premium", 50)],
        )

    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.pre_checkout_query.answer(ok=True)

    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ Could not activate Premium — user not found. Please contact support.")
            return
        self.user_service.update_plan(db_user.id, UserPlan.PREMIUM)
        await update.message.reply_text(
            "🎉 *Premium activated!*\n\n"
            "You now have unlimited subscriptions.\n"
            "Use /setschedule <hours> to customize check frequency.",
            parse_mode="Markdown",
        )

    async def setschedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ Please use /start first.")
            return

        if db_user.plan == UserPlan.FREE:
            await update.message.reply_text(
                "⚠️ Custom schedules are a Premium feature.\nUse /premium to upgrade."
            )
            return

        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /setschedule <hours>\nExample: /setschedule 2")
            return

        hours = int(context.args[0])
        if hours < 1 or hours > 24:
            await update.message.reply_text("❌ Hours must be between 1 and 24.")
            return

        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)
        for sub in subscriptions:
            self.subscription_service.update_subscription(sub.id, interval_hours=hours)

        await update.message.reply_text(
            f"✅ All your subscriptions will now check every {hours}h."
        )

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.admin_id or update.effective_user.id != self.admin_id:
            return

        args = context.args

        if not args:
            await update.message.reply_text(
                "*Admin commands:*\n"
                "/admin users — list all users\n"
                "/admin stats — usage statistics\n"
                "/admin premium <telegram\\_id> — upgrade user\n"
                "/admin free <telegram\\_id> — downgrade user",
                parse_mode="Markdown",
            )
            return

        if args[0] == "users":
            with self.db.get_session() as session:
                users = session.query(User).order_by(User.created_at.desc()).all()
                if not users:
                    await update.message.reply_text("No users yet.")
                    return
                lines = []
                for u in users:
                    sub_count = session.query(Subscription).filter_by(user_id=u.id).count()
                    name = (u.username or u.first_name or str(u.telegram_id)).replace('_', '\\_')
                    lines.append(f"`{u.telegram_id}` @{name} — {u.plan.value} — {sub_count} subs")
                await update.message.reply_text(
                    "*All users:*\n" + "\n".join(lines),
                    parse_mode="Markdown",
                )

        elif args[0] == "stats":
            with self.db.get_session() as session:
                user_count = session.query(User).count()
                premium_count = session.query(User).filter_by(plan=UserPlan.PREMIUM).count()
                sub_count = session.query(Subscription).count()
                await update.message.reply_text(
                    f"*Stats:*\n"
                    f"Users: {user_count} ({premium_count} premium)\n"
                    f"Subscriptions: {sub_count}",
                    parse_mode="Markdown",
                )

        elif args[0] in ("premium", "free") and len(args) > 1:
            try:
                target_id = int(args[1])
            except ValueError:
                await update.message.reply_text("❌ Invalid telegram_id — must be a number.")
                return
            target_user = self.user_service.get_user_by_telegram_id(target_id)
            if not target_user:
                await update.message.reply_text(f"❌ User {target_id} not found.")
                return
            new_plan = UserPlan.PREMIUM if args[0] == "premium" else UserPlan.FREE
            self.user_service.update_plan(target_user.id, new_plan)
            await update.message.reply_text(
                f"✅ User `{target_id}` is now *{new_plan.value}*.",
                parse_mode="Markdown",
            )

        else:
            await update.message.reply_text("❌ Unknown command. Use /admin for help.")
