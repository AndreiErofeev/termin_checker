# Premium Upsell & Ad Slot Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Motivate free users to buy premium through in-context nudges and a reserved ad slot, without causing churn. Premium purchase is NOT enabled yet — all CTAs show "coming soon".

**Architecture:** Ad footer helper + `bot_settings` key-value table + admin ad commands. No new service class. All changes are in `handlers.py`, `i18n.py`, `database.py`.

**Tech Stack:** python-telegram-bot v21, SQLAlchemy + SQLite, existing i18n system (`t(lang, key)`).

---

## Constraints

- **Premium is disabled.** `/premium` and the `get_premium` callback both show `premium_unavailable` (with "coming soon" appended). Mark every relevant code point with `# TODO: remove when premium goes live`.
- **No proactive push messages.** All nudges appear only in response to user actions.
- **Multilanguage.** All bot-generated strings use `t(lang, key)`. Paid ads (set by admin) are single-language raw text — that's fine.
- **Free users only see ads.** Premium users never see the footer or upsell buttons.

---

## Section 1: Ad Slot System

### `_ad_footer(lang, user) -> str | None`

New private method on `BotHandlers`. Returns:
- `None` if `user.plan == UserPlan.PREMIUM`
- Raw `value` from `bot_settings` where `key = 'current_ad'`, if that row exists
- Otherwise: `t(lang, "ad_premium_upsell")` (the default premium upsell string)

The footer is appended with `"\n\n" + footer` to:
1. `no_apts` check result messages
2. `found_apts` check result messages (both paths in `_run_check_and_reply`)
3. `subscribed` confirmation (after `_create_subscription` succeeds)

### New i18n keys

`ad_premium_upsell` — short, value-focused, not pushy:

| lang | text |
|------|------|
| en | `⭐ *Free plan:* checks every 12h. Premium checks every 1h — catch slots 12× faster. /premium` |
| de | `⭐ *Kostenlos:* Prüfung alle 12h. Premium prüft stündlich — 12× schneller. /premium` |
| ru | `⭐ *Бесплатно:* проверка каждые 12ч. Premium — каждый час, в 12 раз чаще. /premium` |
| uk | `⭐ *Безкоштовно:* перевірка кожні 12год. Premium — щогодини, у 12 разів частіше. /premium` |
| tr | `⭐ *Ücretsiz:* 12 saatte bir kontrol. Premium saatte bir kontrol — 12× daha hızlı. /premium` |

`ad_premium_upsell` uses Markdown bold. All check result messages already use `parse_mode="Markdown"`.

---

## Section 2: Hard-Limit Upgrade Prompts

Two existing hard-limit messages get an inline `[⭐ Get Premium (coming soon)]` button added:

1. **3-sub cap** — `plan_limit` message in `_create_subscription`
2. **`/setschedule` blocked** — `premium_only` message in `setschedule_command`

Button label: `t(lang, "btn_get_premium")` — new i18n key.

| lang | text |
|------|------|
| en | `⭐ Get Premium (coming soon)` |
| de | `⭐ Premium holen (demnächst)` |
| ru | `⭐ Получить Premium (скоро)` |
| uk | `⭐ Отримати Premium (скоро)` |
| tr | `⭐ Premium Al (yakında)` |

Button callback: `get_premium`. Handler in `button_callback` dispatches to `premium_command` logic (shows unavailable message). Mark with `# TODO: remove when premium goes live — trigger invoice instead`.

Both limit messages switch from `query.edit_message_text(text)` to `query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[btn]]))`.

---

## Section 3: Premium Command (disabled, coming soon)

`premium_command` keeps its early return. Update the `premium_unavailable` i18n strings to append "(coming soon)" / "(скоро)" / "(demnächst)" / "(незабаром)" / "(yakında)".

Mark the early-return line: `# TODO: remove when premium goes live`.

No invoice is triggered anywhere.

---

## Section 4: `bot_settings` Table + Admin Commands

### Migration

New table: `bot_settings(key TEXT PRIMARY KEY, value TEXT NOT NULL)`.

Add to `apply_migrations()` in `database.py`:

```python
conn.execute(sqlalchemy.text(
    "CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
))
conn.commit()
```

(Uses `CREATE TABLE IF NOT EXISTS` — already idempotent, no try/except needed.)

### Admin subcommands

Extend the `admin_command` handler with three new `args[0]` branches:

**`/admin ad set <text>`** — upserts `current_ad` row:
```python
elif args[0] == "ad" and len(args) >= 3 and args[1] == "set":
    ad_text = " ".join(args[2:])
    with self.db.get_session() as session:
        session.execute(sqlalchemy.text(
            "INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('current_ad', :v)"
        ), {"v": ad_text})
        session.commit()
    await update.message.reply_text(f"✅ Ad text set:\n{ad_text}")
```

**`/admin ad clear`** — deletes the row:
```python
elif args[0] == "ad" and len(args) == 2 and args[1] == "clear":
    with self.db.get_session() as session:
        session.execute(sqlalchemy.text(
            "DELETE FROM bot_settings WHERE key = 'current_ad'"
        ))
        session.commit()
    await update.message.reply_text("✅ Ad cleared — using default premium upsell.")
```

**`/admin ad show`** — reads current value:
```python
elif args[0] == "ad" and len(args) == 2 and args[1] == "show":
    with self.db.get_session() as session:
        row = session.execute(sqlalchemy.text(
            "SELECT value FROM bot_settings WHERE key = 'current_ad'"
        )).fetchone()
    if row:
        await update.message.reply_text(f"Current ad:\n{row[0]}")
    else:
        await update.message.reply_text("No custom ad set — showing premium upsell.")
```

Update `/admin` help text to include: `/admin ad set <text>`, `/admin ad clear`, `/admin ad show`.

### `_ad_footer` DB lookup

```python
def _ad_footer(self, lang: str, user) -> str | None:
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

---

## Files Changed

| File | Change |
|------|--------|
| `src/core/database.py` | Add `CREATE TABLE IF NOT EXISTS bot_settings` to `apply_migrations()` |
| `src/bot/i18n.py` | Add `ad_premium_upsell` and `btn_get_premium` keys (5 languages); update `premium_unavailable` to include "coming soon" |
| `src/bot/handlers.py` | Add `_ad_footer()`, update `_run_check_and_reply`, `_create_subscription`, `setschedule_command`, `button_callback`, `premium_command`, `admin_command` |

No new files. No new service class. ~80 lines net added.

---

## What Free Users Experience

| Touchpoint | What they see |
|-----------|---------------|
| Check result (no slots) | Result message + ad footer |
| Check result (slots found) | Result message + ad footer |
| New subscription confirmed | Confirmation + ad footer |
| Hit 3-sub cap | Limit message + `[⭐ Get Premium (coming soon)]` button |
| Try `/setschedule` | Premium-only message + `[⭐ Get Premium (coming soon)]` button |
| Tap "Get Premium" button | "Premium coming soon" message |
| `/premium` command | "Premium coming soon" message |

Premium users see none of the above.

---

## What Premium Looks Like When Enabled

When you're ready to go live:
1. Remove early return in `premium_command` (marked `# TODO`)
2. Remove "coming soon" from `premium_unavailable` strings (or swap to the invoice flow)
3. Update `button_callback` `get_premium` branch to send invoice (marked `# TODO`)
4. Update `btn_get_premium` i18n to drop "(coming soon)"
5. Set XTR price (~230 XTR ≈ €2.99 at current rates)
