# Improvement Roadmap

Prioritized by impact vs effort. P1 = do next, P3 = do when MRR justifies it.

---

## P1 — Monetization (unlock revenue)

### Enable Premium (Telegram Stars)
Currently disabled with "coming soon". The entire payment flow is already coded — just remove the early return and set the correct XTR price (~230 XTR ≈ €2.99 at current rates).
TODOs in code are already marked.

### One-time "monitor until found" purchase
User pays €0.99 once, bot monitors indefinitely and stops automatically when a slot is found. No monthly commitment. Targets users who refuse subscriptions. Likely higher conversion than monthly for the Führerschein audience (one-time need).

---

## P1 — User Experience (retention)

### Direct booking link in notifications
When a slot is found, include a direct URL to the TEVIS booking page for that service. Users currently have to navigate TEVIS themselves and the slot may be gone. One tap to book is the biggest UX gap right now.

### "Slot gone before I could book" problem
Add a re-check button to the "found" notification: `[🔄 Re-check now]`. When the user clicks it, the bot confirms whether the slot is still available. Reduces frustration from race conditions.

### Appointment date/time filtering
Let users set preferences: "only morning slots", "only after 2026-05-01", "weekdays only". Reduces noise for users who can't take any slot — they only get notified when a usable one appears. Requires storing filter params per subscription.

---

## P2 — Core reliability

### Scraper health monitoring
No alerting exists when the scraper silently fails (TEVIS changes DOM, Playwright crashes, site is down). Implement: if a subscription hasn't had a successful check in >2× its interval, send the admin a Telegram alert. Low effort, high value.

### SQLite → PostgreSQL (when needed)
SQLite with `check_same_thread=False` and `StaticPool` works fine for ~1000 users but will hit write-lock issues under load. Migrate when premium users > 200 or concurrent requests cause errors. PostgreSQL connection string is already supported in `database.py`.

### DB backups to S3
Currently no automated backup. EC2 instance data would be lost if the instance is terminated. Add a daily cron job that copies `termin.db` to S3 (same bucket already used for service schema). ~10 lines of bash.

---

## P2 — Growth features

### Service name translations (Phase 2)
Design doc already written at `docs/phase2-service-translations.md`. DeepL API, on-demand translation with caching in `services.translations` column. Build when users start asking "what does X service mean?"

### Referral system
`/refer` generates a personal link. When someone starts the bot via that link, the referrer gets 1 extra free subscription slot (or extended check interval). Zero ad spend needed for growth in Telegram communities.

### Notification when appointment disappears
Currently the bot only notifies when slots appear. If a user got notified but couldn't book in time, there's no "slot gone" notification. Send a follow-up: "❌ That slot was taken. Still watching for new ones." Keeps users informed and reduces unsubscribes from disappointed users.

---

## P2 — Admin/operations

### Admin broadcast command
`/admin broadcast <text>` — sends a message to all active users (or all free users). Needed for: announcing premium launch, announcing new services, sending paid ad blasts. Currently no way to reach users in bulk.

### Analytics command
`/admin analytics` — shows: top 5 most-subscribed services, free/premium conversion rate, avg check-to-found time, most active hour of day. Helps decide which features to build and which services to highlight in marketing.

### User timezone setting
All timestamps currently shown in Berlin time (hardcoded). Users in Ukraine, Turkey, or other timezones see confusing times. Add a `/timezone` command or auto-detect from Telegram's `language_code`.

---

## P3 — Monetization expansion

### Auto-booking (premium tier 2)
Bot automatically books the first available slot, not just notifies. This is how Visard.io/VisaCatcher work for Schengen visas and why they charge £100. Requires TEVIS login credentials per user (significant complexity + legal risk — check TEVIS ToS first).

### B2B: notify multiple people for one service
"Group subscription" — one user pays, multiple Telegram IDs get notified (e.g., a family where multiple members need Führerschein conversion). €4.99/month as mentioned in marketing doc. Simple to implement once premium is live.

### Sell ad slots programmatically
Currently admin sets ads manually via `/admin ad set`. Later: a simple web form where advertisers submit text + pay via Stripe, bot activates automatically. Only worth building when ad demand > 1 buyer/month.

---

## P3 — Infrastructure

### Multi-city support
TEVIS is Düsseldorf-specific. Other German cities have similar portals (Berlin Bürgeramt, Munich KVR). Expanding requires per-city scrapers and service schemas. High effort, but opens a much larger market. Design the schema to be city-aware from the start before user data grows.

### Web landing page + SEO
A single static page (`terminbot.de` or similar) targeting search queries like "TEVIS Düsseldorf Bot" and "Termin Düsseldorf Führerschein". Google Ads mentioned in marketing doc as €20-30/month experiment. Page also improves trust for users who Google the bot before using it.

---

## Known bugs / tech debt

| Issue | Priority | Notes |
|-------|----------|-------|
| `session.commit()` called twice in some `with db.get_session()` blocks | Low | Harmless but noisy; context manager commits on exit |
| Test imports mid-file in `test_premium_upsell.py` | Low | Style issue, not functional |
| `premium_command` has unreachable dead code below early return | Medium | Clean up when premium is enabled |
| Admin ad commands have no unit tests | Medium | SQL is trivial but coverage gap |

---

*Last updated: 2026-04-20*
