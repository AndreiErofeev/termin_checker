# Termin Checker — Telegram Bot Design

**Date:** 2026-04-18
**Status:** Approved

## Overview

A Telegram bot that lets users subscribe to Düsseldorf appointment services and get notified when slots open. Menu is driven by the S3 schema refreshed monthly by the existing Lambda scraper. Slot checking uses Playwright (existing `AppointmentChecker`). Runs on a single EC2 `t3.micro`.

## Architecture

One EC2 `t3.micro` runs a single Python process with four responsibilities:

- **Telegram bot** — polling mode, handles user commands
- **APScheduler** — fires periodic checks per subscription
- **Playwright checker** — navigates TEVIS site, extracts available slots
- **SQLite** — persists users, subscriptions, check history

At startup the bot reads `termin/schema.json` from S3 and upserts all departments + services into the `services` table. This keeps the menu in sync with the monthly Lambda scrape without any manual intervention.

```
EC2 t3.micro
├── Telegram polling
├── APScheduler → AppointmentChecker (Playwright)
├── SQLite (termin.db)
└── S3 read (menu schema, on startup)
```

## User Flow

```
/subscribe  → pick department (inline keyboard)
            → pick service
            → subscription created (checks 2×/day by default)

[Scheduler fires]
            → Playwright check runs
            → slots found: Telegram notification with dates/times
            → no slots: silent

/list       → active subscriptions + last check time
/check      → immediate on-demand check
/unsubscribe → remove subscription
/premium    → Stars invoice → on payment: upgrade plan
/setschedule <hours> → premium only, set custom interval
```

## Data Model

Uses existing `src/core/models.py` without changes.

| Table | Key fields |
|---|---|
| `users` | `telegram_id`, `plan` (free/premium) |
| `services` | `category`, `service_name` — populated from S3 |
| `subscriptions` | `user_id`, `service_id`, `interval_hours` (12 = free default) |
| `checks` | history per subscription run |
| `appointments` | slots found per check (date, time) |

## Tiers

| | Free | Premium |
|---|---|---|
| Subscriptions | 3 max | Unlimited |
| Check frequency | 2×/day (every 12h) | Custom (`interval_hours`) |
| Auto-booking | No | Future |
| Price | Free | Telegram Stars (e.g. 50 XTR/month) |

Premium is activated via Telegram Stars payment (`/premium` → `send_invoice` with `currency="XTR"`). On successful `PreCheckoutQuery` + `SuccessfulPayment` callback: set `user.plan = premium`. No expiry tracking in v1.

## Components

### What exists (wire up / minor fixes)
- `src/core/models.py` — no changes
- `src/core/appointment_checker.py` — no changes
- `src/bot/handlers.py` — needs S3 menu wired in for `/subscribe`
- `src/bot/main.py` — needs scheduler started alongside bot
- `src/services/user_service.py`, `subscription_service.py` — mostly usable

### What needs building
1. **`src/core/schema_loader.py`** — reads S3 JSON, upserts `services` rows on startup
2. **`src/services/check_service.py`** — runs `AppointmentChecker`, writes `Check` + `Appointment` rows, triggers notification
3. **`src/services/scheduler.py`** — wire APScheduler to `check_service`, respect `interval_hours` per subscription
4. **`src/services/notification_service.py`** — send Telegram message listing found slots
5. **Premium handlers** in `src/bot/handlers.py` — Stars invoice, payment callbacks, `/setschedule`
6. **EC2 setup** — `systemd` unit, `.env`, Chromium `dnf` deps (same list as Dockerfile)

## EC2 Deployment

- **Instance:** `t3.micro`, Amazon Linux 2023
- **Chromium deps:** same `dnf install` list as Dockerfile (already proven working)
- **Process manager:** `systemd` service — auto-restart on crash, start on boot
- **Config:** `.env` file with `TELEGRAM_BOT_TOKEN`, `S3_BUCKET`, `AWS_REGION`
- **IAM:** instance profile with existing S3 read policy (`infra/iam/lambda-s3-policy.json` + `s3:GetObject`)
- **DB:** SQLite at `/var/app/termin.db`
- **No webhook** — polling is simpler and reliable for a single bot

## Out of Scope (v1)

- Web UI
- Email notifications
- Auto-booking form fill (Premium v2)
- Payment expiry / subscription renewal tracking
