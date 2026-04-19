# Premium Upsell & Ad Slot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add in-context premium upsell nudges and a swappable ad slot for free users, without enabling actual purchases yet.

**Architecture:** Four small changes across three files — i18n strings, a DB migration, a `_ad_footer()` helper wired into check results, and admin commands to manage ad text. No new files, no new service classes.

**Tech Stack:** python-telegram-bot v21, SQLAlchemy + SQLite raw `sqlalchemy.text()`, existing `t(lang, key)` i18n system.

---

## File Map

| File | What changes |
|------|-------------|
| `src/bot/i18n.py` | Add `ad_premium_upsell`, `btn_get_premium` keys (5 langs); update `premium_unavailable` to append "(coming soon)" |
| `src/core/database.py` | Add `CREATE TABLE IF NOT EXISTS bot_settings` to `apply_migrations()` |
| `src/bot/handlers.py` | Add `import sqlalchemy`; add `_ad_footer()`; wire footer into `_run_check_and_reply` + `_create_subscription`; add inline buttons to limit messages; handle `get_premium` callback; add `# TODO` on `premium_command`; add admin ad subcommands |
| `tests/test_premium_upsell.py` | New test file — `_ad_footer` unit tests |

---

### Task 1: i18n new strings + `bot_settings` migration

**Files:**
- Modify: `src/bot/i18n.py`
- Modify: `src/core/database.py:82-93`
- Test: `tests/test_premium_upsell.py` (create)

- [ ] **Step 1: Write failing tests for new i18n keys**

Create `tests/test_premium_upsell.py`:

```python
from src.bot.i18n import t


def test_ad_premium_upsell_en():
    result = t("en", "ad_premium_upsell")
    assert "12h" in result
    assert "/premium" in result


def test_ad_premium_upsell_ru():
    result = t("ru", "ad_premium_upsell")
    assert "12" in result


def test_ad_premium_upsell_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "ad_premium_upsell")
        assert result  # not empty, not the key itself


def test_btn_get_premium_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "btn_get_premium")
        assert result
        assert "coming" in result.lower() or "скоро" in result or "demnächst" in result or "незабаром" in result or "yakında" in result


def test_premium_unavailable_has_coming_soon():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "premium_unavailable")
        assert any(s in result for s in ("coming soon", "demnächst", "скоро", "незабаром", "yakında"))
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_premium_upsell.py -v
```
Expected: FAILED (KeyError or assertion error — keys don't exist yet)

- [ ] **Step 3: Add new i18n keys and update `premium_unavailable`**

In `src/bot/i18n.py`, add to each language block (after `language_set`):

**English (`"en"`)** — add after `"language_set"`:
```python
"ad_premium_upsell": (
    "⭐ *Free plan:* checks every 12h. Premium checks every 1h — catch slots 12× faster. /premium"
),
"btn_get_premium": "⭐ Get Premium (coming soon)",
```
And update:
```python
"premium_unavailable": "🚧 Premium subscriptions are temporarily unavailable (coming soon). Check back soon!",
```

**German (`"de"`)** — add after `"language_set"`:
```python
"ad_premium_upsell": (
    "⭐ *Kostenlos:* Prüfung alle 12h. Premium prüft stündlich — 12× schneller. /premium"
),
"btn_get_premium": "⭐ Premium holen (demnächst)",
```
And update:
```python
"premium_unavailable": "🚧 Premium-Abonnements sind vorübergehend nicht verfügbar (demnächst).",
```

**Russian (`"ru"`)** — add after `"language_set"`:
```python
"ad_premium_upsell": (
    "⭐ *Бесплатно:* проверка каждые 12ч. Premium — каждый час, в 12 раз чаще. /premium"
),
"btn_get_premium": "⭐ Получить Premium (скоро)",
```
And update:
```python
"premium_unavailable": "🚧 Premium-подписки временно недоступны (скоро).",
```

**Ukrainian (`"uk"`)** — add after `"language_set"`:
```python
"ad_premium_upsell": (
    "⭐ *Безкоштовно:* перевірка кожні 12год. Premium — щогодини, у 12 разів частіше. /premium"
),
"btn_get_premium": "⭐ Отримати Premium (незабаром)",
```
And update:
```python
"premium_unavailable": "🚧 Premium-підписки тимчасово недоступні (незабаром).",
```

**Turkish (`"tr"`)** — add after `"language_set"`:
```python
"ad_premium_upsell": (
    "⭐ *Ücretsiz:* 12 saatte bir kontrol. Premium saatte bir kontrol — 12× daha hızlı. /premium"
),
"btn_get_premium": "⭐ Premium Al (yakında)",
```
And update:
```python
"premium_unavailable": "🚧 Premium abonelikler şu anda kullanılamıyor (yakında).",
```

- [ ] **Step 4: Add `bot_settings` table to migration**

In `src/core/database.py`, inside `apply_migrations()`, add after the existing `try/except` block:

```python
with self.engine.connect() as conn:
    conn.execute(sqlalchemy.text(
        "CREATE TABLE IF NOT EXISTS bot_settings "
        "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    ))
    conn.commit()
    logger.info("Migration applied: bot_settings table ensured")
```

The full `apply_migrations` method should now be:

```python
def apply_migrations(self):
    """Add any missing columns to existing tables (idempotent)."""
    import sqlalchemy
    with self.engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text(
                "ALTER TABLE users ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'en'"
            ))
            conn.commit()
            logger.info("Migration applied: users.language column added")
        except Exception:
            pass  # Column already exists

    with self.engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS bot_settings "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        ))
        conn.commit()
        logger.info("Migration applied: bot_settings table ensured")
```

- [ ] **Step 5: Run tests**

```
pytest tests/test_premium_upsell.py -v
```
Expected: all 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/bot/i18n.py src/core/database.py tests/test_premium_upsell.py
git commit -m "feat: add premium upsell i18n strings and bot_settings migration"
```

---

### Task 2: `_ad_footer()` helper + wire into check results

**Files:**
- Modify: `src/bot/handlers.py`
- Test: `tests/test_premium_upsell.py`

- [ ] **Step 1: Write failing tests for `_ad_footer`**

Append to `tests/test_premium_upsell.py`:

```python
import sqlalchemy
from src.core.database import init_database
from src.core.models import UserPlan
from src.bot.handlers import BotHandlers


def _make_db():
    db = init_database("sqlite:///:memory:")
    db.create_tables()
    db.apply_migrations()
    return db


class _FreeUser:
    plan = UserPlan.FREE


class _PremiumUser:
    plan = UserPlan.PREMIUM


def test_ad_footer_free_returns_premium_upsell():
    db = _make_db()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _FreeUser())
    assert result is not None
    assert "12h" in result


def test_ad_footer_premium_returns_none():
    db = _make_db()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _PremiumUser())
    assert result is None


def test_ad_footer_custom_ad_overrides_upsell():
    db = _make_db()
    with db.engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "INSERT INTO bot_settings (key, value) VALUES ('current_ad', 'Sponsor message here')"
        ))
        conn.commit()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _FreeUser())
    assert result == "Sponsor message here"


def test_ad_footer_custom_ad_not_shown_to_premium():
    db = _make_db()
    with db.engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "INSERT INTO bot_settings (key, value) VALUES ('current_ad', 'Sponsor message here')"
        ))
        conn.commit()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _PremiumUser())
    assert result is None


def test_ad_footer_respects_language():
    db = _make_db()
    handlers = BotHandlers(db)
    result_ru = handlers._ad_footer("ru", _FreeUser())
    assert "12" in result_ru
    result_en = handlers._ad_footer("en", _FreeUser())
    assert result_en != result_ru
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_premium_upsell.py::test_ad_footer_free_returns_premium_upsell -v
```
Expected: FAILED — `BotHandlers` has no `_ad_footer` method

- [ ] **Step 3: Add `import sqlalchemy` to handlers.py**

At the top of `src/bot/handlers.py`, add after the existing imports:

```python
import sqlalchemy
```

- [ ] **Step 4: Add `_ad_footer()` method to `BotHandlers`**

Add after the `_dept_keyboard` method (before `# ── Commands`):

```python
def _ad_footer(self, lang: str, user) -> str | None:
    """Return ad text for free users, None for premium. Checks DB for custom ad first."""
    if user.plan == UserPlan.PREMIUM:
        return None
    with self.db.get_session() as session:
        row = session.execute(sqlalchemy.text(
            "SELECT value FROM bot_settings WHERE key = 'current_ad'"
        )).fetchone()
    if row:
        return row[0]
    return t(lang, "ad_premium_upsell")
```

- [ ] **Step 5: Run tests**

```
pytest tests/test_premium_upsell.py -v
```
Expected: all tests added so far PASS

- [ ] **Step 6: Wire footer into `_run_check_and_reply` and `_create_subscription`**

`_run_check_and_reply` needs a `user` parameter to pass to `_ad_footer`. Change its signature and both call sites:

**Change signature** (line ~373):
```python
async def _run_check_and_reply(self, query, subscription_id: int, lang: str = "en", user=None):
```

**Inside `_run_check_and_reply`**, replace the `no_apts` reply and the `found_apts` reply:

Found-appointments path (was `await query.edit_message_text(message, parse_mode="Markdown")`):
```python
footer = self._ad_footer(lang, user) if user else None
if footer:
    message += "\n\n" + footer
await query.edit_message_text(message, parse_mode="Markdown")
```

No-appointments path (was `await query.edit_message_text(t(lang, "no_apts"))`):
```python
no_apts_text = t(lang, "no_apts")
footer = self._ad_footer(lang, user) if user else None
if footer:
    no_apts_text += "\n\n" + footer
await query.edit_message_text(no_apts_text, parse_mode="Markdown")
```

**Update call site in `_create_subscription`** — append footer to the `subscribed` message AND pass user to `_run_check_and_reply`:

Replace the success block (currently lines ~355-362):
```python
if subscription:
    service = subscription.service
    freq = t(lang, "freq_twice_daily") if is_free else t(lang, "freq_every_nh", n=interval_hours)
    subscribed_text = t(lang, "subscribed", name=service.service_name, freq=freq)
    footer = self._ad_footer(lang, db_user)
    if footer:
        subscribed_text += "\n\n" + footer
    await query.edit_message_text(subscribed_text, parse_mode="Markdown")
    await self._run_check_and_reply(query, subscription.id, lang, user=db_user)
else:
    await query.edit_message_text(t(lang, "already_subscribed"))
```

**Update call site in `_handle_manual_check`** — fetch user and pass it:
```python
async def _handle_manual_check(self, query, subscription_id: int, lang: str = "en"):
    db_user = self.user_service.get_user_by_telegram_id(query.from_user.id)
    await query.edit_message_text(t(lang, "checking"))
    await self._run_check_and_reply(query, subscription_id, lang, user=db_user)
```

- [ ] **Step 7: Run full test suite**

```
pytest tests/ -v
```
Expected: all tests PASS (no regressions)

- [ ] **Step 8: Commit**

```bash
git add src/bot/handlers.py tests/test_premium_upsell.py
git commit -m "feat: add _ad_footer helper and wire into check results"
```

---

### Task 3: Hard-limit upgrade buttons + `get_premium` callback + TODO comment

**Files:**
- Modify: `src/bot/handlers.py`

No new tests needed for this task — the inline button wiring is integration-level and the callback logic is trivial (just shows a message).

- [ ] **Step 1: Add inline "Get Premium" button to `plan_limit` message**

In `_create_subscription`, replace the free-tier limit early return (currently `await query.edit_message_text(t(lang, "plan_limit"))`):

```python
if len(existing) >= 3:
    btn = InlineKeyboardButton(t(lang, "btn_get_premium"), callback_data="get_premium")
    await query.edit_message_text(
        t(lang, "plan_limit"),
        reply_markup=InlineKeyboardMarkup([[btn]]),
    )
    return
```

- [ ] **Step 2: Add inline "Get Premium" button to `setschedule_command` premium-only message**

In `setschedule_command`, replace the free-user block (currently `await update.message.reply_text(t(lang, "premium_only"))`):

```python
if db_user.plan == UserPlan.FREE:
    btn = InlineKeyboardButton(t(lang, "btn_get_premium"), callback_data="get_premium")
    await update.message.reply_text(
        t(lang, "premium_only"),
        reply_markup=InlineKeyboardMarkup([[btn]]),
    )
    return
```

- [ ] **Step 3: Handle `get_premium` callback in `button_callback`**

In `button_callback`, add a new branch after the `cancel` handler (after `if data == "cancel":`):

```python
elif data == "get_premium":
    # TODO: remove when premium goes live — trigger invoice instead
    await query.edit_message_text(t(lang, "premium_unavailable"))
```

- [ ] **Step 4: Add TODO comment to `premium_command`**

In `premium_command`, the early return currently reads:
```python
await update.message.reply_text(t(lang, "premium_unavailable"))
return
```

Change to:
```python
# TODO: remove when premium goes live
await update.message.reply_text(t(lang, "premium_unavailable"))
return
```

- [ ] **Step 5: Run full test suite**

```
pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/bot/handlers.py
git commit -m "feat: add Get Premium buttons on free-tier limits and get_premium callback"
```

---

### Task 4: Admin ad commands

**Files:**
- Modify: `src/bot/handlers.py` (admin section only)

- [ ] **Step 1: Update admin help text**

In `admin_command`, the help text block (currently shows 4 commands) — add the ad commands:

```python
await update.message.reply_text(
    "*Admin commands:*\n"
    "/admin users — list all users\n"
    "/admin stats — usage statistics\n"
    "/admin premium <telegram\\_id> — upgrade user\n"
    "/admin free <telegram\\_id> — downgrade user\n"
    "/admin ad set <text> — set custom ad for free users\n"
    "/admin ad clear — revert to premium upsell\n"
    "/admin ad show — show current ad text",
    parse_mode="Markdown",
)
```

- [ ] **Step 2: Add ad subcommands**

In `admin_command`, add a new `elif` block before the final `else` branch:

```python
elif args[0] == "ad":
    if len(args) >= 3 and args[1] == "set":
        ad_text = " ".join(args[2:])
        with self.db.get_session() as session:
            session.execute(sqlalchemy.text(
                "INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('current_ad', :v)"
            ), {"v": ad_text})
            session.commit()
        await update.message.reply_text(f"✅ Ad text set:\n\n{ad_text}")

    elif len(args) == 2 and args[1] == "clear":
        with self.db.get_session() as session:
            session.execute(sqlalchemy.text(
                "DELETE FROM bot_settings WHERE key = 'current_ad'"
            ))
            session.commit()
        await update.message.reply_text("✅ Ad cleared — reverting to premium upsell.")

    elif len(args) == 2 and args[1] == "show":
        with self.db.get_session() as session:
            row = session.execute(sqlalchemy.text(
                "SELECT value FROM bot_settings WHERE key = 'current_ad'"
            )).fetchone()
        if row:
            await update.message.reply_text(f"Current ad:\n\n{row[0]}")
        else:
            await update.message.reply_text("No custom ad — showing premium upsell to free users.")

    else:
        await update.message.reply_text("Usage: /admin ad set <text> | clear | show")
```

- [ ] **Step 3: Run full test suite**

```
pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add src/bot/handlers.py
git commit -m "feat: add admin ad set/clear/show commands"
```

---

### Task 5: Deploy to EC2

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Deploy**

```bash
ssh -i ~/.ssh/termin-bot.pem ec2-user@$(aws ec2 describe-instances \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text --region eu-west-1) \
  "cd /var/app && git pull && sudo systemctl restart termin-bot && sleep 2 && sudo systemctl status termin-bot --no-pager"
```

Expected: service shows `active (running)` with a fresh start timestamp.
