"""
Telegram Bot Command Handlers

Handles all bot commands and user interactions.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes

from ..core.database import Database
from ..services import UserService, SubscriptionService, CheckService
from ..core.models import Service, UserPlan, User, Subscription

logger = logging.getLogger(__name__)


class BotHandlers:
    """Handler class for bot commands"""

    def __init__(self, db: Database):
        self.db = db
        self.user_service = UserService(db)
        self.subscription_service = SubscriptionService(db)
        self.check_service = CheckService(db)
        self.admin_id = int(os.environ.get("ADMIN_TELEGRAM_ID", 0))

    # ── Navigation helpers ────────────────────────────────────────────────

    def _sorted_depts(self, session) -> list[tuple[str, int]]:
        """Sorted list of (dept_name, service_count)."""
        services = session.query(Service).filter(Service.active == True).all()
        depts: dict[str, int] = {}
        for s in services:
            dept = s.department or "Other"
            depts[dept] = depts.get(dept, 0) + 1
        return sorted(depts.items())

    def _sorted_cats(self, session, dept_name: str) -> list[tuple[str, int]]:
        """Sorted list of (category_name, service_count) for a dept."""
        services = session.query(Service).filter(
            Service.department == dept_name,
            Service.active == True,
        ).all()
        cats: dict[str, int] = {}
        for s in services:
            cats[s.category] = cats.get(s.category, 0) + 1
        return sorted(cats.items())

    def _dept_keyboard(self, depts: list[tuple[str, int]], cancel=True) -> InlineKeyboardMarkup:
        """2-column dept keyboard. callback_data = d{idx}."""
        rows = []
        items = list(depts)
        for i in range(0, len(items), 2):
            row = []
            for j in range(2):
                if i + j < len(items):
                    name, count = items[i + j]
                    label = name if len(name) <= 28 else name[:26] + "…"
                    row.append(InlineKeyboardButton(f"{label} ({count})", callback_data=f"d{i+j}"))
            rows.append(row)
        if cancel:
            rows.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        return InlineKeyboardMarkup(rows)

    # ── Commands ──────────────────────────────────────────────────────────

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.create_or_update_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        await update.message.reply_text(
            f"👋 Welcome {user.first_name}!\n\n"
            "This bot monitors appointment availability for Düsseldorf city services.\n\n"
            "Commands:\n"
            "/subscribe - Subscribe to a service\n"
            "/list - View your subscriptions\n"
            "/unsubscribe - Cancel a subscription\n"
            "/check - Run manual check\n"
            "/help - Help\n\n"
            f"Your plan: {db_user.plan.value.upper()}"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 *Help & Commands*\n\n"
            "/start - Start the bot\n"
            "/subscribe - Subscribe to appointment notifications\n"
            "/list - View your active subscriptions\n"
            "/unsubscribe - Cancel a subscription\n"
            "/check - Manually check for appointments\n"
            "/help - This message\n\n"
            "*How it works:*\n"
            "1. Subscribe to a service via /subscribe\n"
            "2. Bot checks automatically and notifies you when slots open\n"
            "3. Manage subscriptions with /list and /unsubscribe\n\n"
            "*Plans:*\n"
            "• FREE: Up to 3 subscriptions, checks every 12 hours\n"
            "• PREMIUM: Unlimited subscriptions, custom schedule",
            parse_mode="Markdown",
        )

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)
        if not subscriptions:
            await update.message.reply_text(
                "📭 You have no active subscriptions.\n\nUse /subscribe to start monitoring a service."
            )
            return

        message = "📋 *Your Active Subscriptions:*\n\n"
        keyboard = []
        for idx, sub in enumerate(subscriptions, 1):
            service = sub.service
            last_check = sub.last_checked_at.strftime("%d.%m.%Y %H:%M") if sub.last_checked_at else "Never"
            message += (
                f"{idx}. *{service.service_name}*\n"
                f"   {service.department or service.category}\n"
                f"   Every {sub.interval_hours}h · Last check: {last_check}\n\n"
            )
            label = service.service_name if len(service.service_name) <= 40 else service.service_name[:38] + "…"
            keyboard.append([InlineKeyboardButton(f"❌ Unsubscribe: {label}", callback_data=f"unsub_{sub.id}")])

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        with self.db.get_session() as session:
            depts = self._sorted_depts(session)
            if not depts:
                await update.message.reply_text("❌ No services available at the moment.")
                return
            await update.message.reply_text(
                "📝 *Select a department:*",
                reply_markup=self._dept_keyboard(depts, cancel=True),
                parse_mode="Markdown",
            )

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)
        if not subscriptions:
            await update.message.reply_text("📭 You have no active subscriptions.")
            return

        keyboard = []
        for sub in subscriptions:
            name = sub.service.service_name
            label = name if len(name) <= 40 else name[:38] + "…"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"unsub_{sub.id}")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        await update.message.reply_text(
            "🗑️ *Select subscription to cancel:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = self.user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text("❌ User not found. Please use /start first.")
            return

        subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)
        if not subscriptions:
            await update.message.reply_text(
                "📭 You have no active subscriptions.\n\nUse /subscribe to start monitoring a service."
            )
            return

        keyboard = []
        for sub in subscriptions:
            name = sub.service.service_name
            label = name if len(name) <= 40 else name[:38] + "…"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"check_{sub.id}")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

        await update.message.reply_text(
            "🔍 *Select subscription to check:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # ── Callback router ───────────────────────────────────────────────────

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "cancel":
            await query.edit_message_text("❌ Cancelled.")

        elif data == "bd":
            await self._show_departments(query)

        elif data.startswith("bc"):
            dept_idx = int(data[2:])
            await self._show_categories(query, dept_idx)

        elif data.startswith("d") and "c" not in data:
            await self._show_categories(query, int(data[1:]))

        elif data.startswith("d") and "c" in data:
            parts = data[1:].split("c")
            await self._show_services(query, int(parts[0]), int(parts[1]))

        elif data.startswith("srv_"):
            await self._create_subscription(query, int(data[4:]))

        elif data.startswith("unsub_"):
            await self._handle_unsubscribe(query, int(data[6:]))

        elif data.startswith("check_"):
            await self._handle_manual_check(query, int(data[6:]))

    # ── Navigation screens ────────────────────────────────────────────────

    async def _show_departments(self, query):
        with self.db.get_session() as session:
            depts = self._sorted_depts(session)
            if not depts:
                await query.edit_message_text("❌ No services available.")
                return
            await query.edit_message_text(
                "📝 *Select a department:*",
                reply_markup=self._dept_keyboard(depts, cancel=True),
                parse_mode="Markdown",
            )

    async def _show_categories(self, query, dept_idx: int):
        with self.db.get_session() as session:
            depts = self._sorted_depts(session)
            if dept_idx >= len(depts):
                await query.edit_message_text("❌ Department not found.")
                return
            dept_name, _ = depts[dept_idx]
            cats = self._sorted_cats(session, dept_name)
            if not cats:
                await query.edit_message_text("❌ No services found in this department.")
                return

            # Skip category screen when there's only one category
            if len(cats) == 1:
                await self._show_services(query, dept_idx, 0)
                return

            keyboard = []
            for j, (cat_name, count) in enumerate(cats):
                label = cat_name if len(cat_name) <= 55 else cat_name[:53] + "…"
                keyboard.append([InlineKeyboardButton(
                    f"{label} ({count})",
                    callback_data=f"d{dept_idx}c{j}",
                )])
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="bd")])

            await query.edit_message_text(
                f"📝 *{dept_name}*\n\nSelect a category:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def _show_services(self, query, dept_idx: int, cat_idx: int):
        with self.db.get_session() as session:
            depts = self._sorted_depts(session)
            if dept_idx >= len(depts):
                await query.edit_message_text("❌ Department not found.")
                return
            dept_name, _ = depts[dept_idx]
            cats = self._sorted_cats(session, dept_name)
            if cat_idx >= len(cats):
                await query.edit_message_text("❌ Category not found.")
                return
            cat_name, _ = cats[cat_idx]

            services = session.query(Service).filter(
                Service.department == dept_name,
                Service.category == cat_name,
                Service.active == True,
            ).all()

            if not services:
                await query.edit_message_text("❌ No services found.")
                return

            keyboard = []
            for service in services[:50]:
                label = service.service_name if len(service.service_name) <= 60 else service.service_name[:58] + "…"
                keyboard.append([InlineKeyboardButton(label, callback_data=f"srv_{service.id}")])
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"bc{dept_idx}")])

            escaped_cat = cat_name.replace("*", "\\*").replace("_", "\\_")
            await query.edit_message_text(
                f"📝 *{escaped_cat}*\n\nSelect a service:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    # ── Actions ───────────────────────────────────────────────────────────

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
                    "Use /premium to upgrade."
                )
                return
            interval_hours = 12
        else:
            interval_hours = 1

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
                f"Checks: {freq}\n\n"
                f"Running first check now...",
                parse_mode="Markdown",
            )
            await self._run_check_and_reply(query, subscription.id)
        else:
            await query.edit_message_text("❌ Already subscribed to this service.")

    async def _handle_unsubscribe(self, query, subscription_id: int):
        success = self.subscription_service.delete_subscription(subscription_id)
        if success:
            await query.edit_message_text("✅ Subscription cancelled.")
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
                    message += f"\n…and {check.appointment_count - 10} more"
                await query.edit_message_text(message, parse_mode="Markdown")
            else:
                await query.edit_message_text(
                    "❌ No appointments available right now.\n\n"
                    "The bot will notify you when slots open up."
                )
        except Exception as e:
            logger.error("Error in check: %s", e, exc_info=True)
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def _handle_manual_check(self, query, subscription_id: int):
        await query.edit_message_text("🔍 Checking for appointments… Please wait.")
        await self._run_check_and_reply(query, subscription_id)

    # ── Premium ───────────────────────────────────────────────────────────

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
            await update.message.reply_text("❌ Could not activate Premium — user not found.")
            return
        self.user_service.update_plan(db_user.id, UserPlan.PREMIUM)
        await update.message.reply_text(
            "🎉 *Premium activated!*\n\nYou now have unlimited subscriptions.\n"
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
            await update.message.reply_text("⚠️ Custom schedules are a Premium feature.\nUse /premium to upgrade.")
            return
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("Usage: /setschedule <hours>\nExample: /setschedule 2")
            return
        hours = int(context.args[0])
        if hours < 1 or hours > 24:
            await update.message.reply_text("❌ Hours must be between 1 and 24.")
            return
        for sub in self.subscription_service.get_user_subscriptions(db_user.id):
            self.subscription_service.update_subscription(sub.id, interval_hours=hours)
        await update.message.reply_text(f"✅ All subscriptions will now check every {hours}h.")

    # ── Admin ─────────────────────────────────────────────────────────────

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
                    name = (u.username or u.first_name or str(u.telegram_id)).replace("_", "\\_")
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
                    f"*Stats:*\nUsers: {user_count} ({premium_count} premium)\nSubscriptions: {sub_count}",
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
