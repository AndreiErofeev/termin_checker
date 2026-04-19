# Marketing Strategy — Termin Checker Bot

**Budget:** €50–100/month for months 1–3, then performance-dependent  
**Goal:** Acquire first 200 active users in 90 days

---

## Competitive Landscape

### Direct competitors — practically none

No commercial service currently monitors TEVIS (Düsseldorf city appointment portal) for end-users. Research found only:

- **Open-source GitHub bots** (berlin-auslaenderbehorde-termin-bot, germany-termin-bot, etc.) — self-hosted, no UI, target developers only. Zero overlap with your audience.
- **Gray market slot resellers** — individuals manually check TEVIS and sell appointment slots on Telegram/VK for **€50–100 per appointment**. This is your most important benchmark: people are already paying that much just to get *one* slot. Your bot at €2–5/month is 20–50x cheaper value.

### Indirect competitors — different problem

These exist and are funded, but solve a different problem (Schengen visa appointments, not German city administration):

| Service | What they do | Price |
|---------|-------------|-------|
| **Visard.io** | Auto-book Schengen visa slots (VFS Global / TLScontact) | £35/31 days (notifications), £100 (auto-booking) |
| **VisaBot (visabot.eu)** | Same, Schengen visa | Paid, pricing not public |
| **VisaCatcher (visacatcher.bot)** | Schengen visa notifications | Free (supported by premium auto-booking) |
| **Visasoon** | Schengen visa auto-booking | Subscription, ~€30–50 |

**Takeaway:** These services prove people pay for appointment notifications. Their pricing (£35–100 per window) validates charging €3–5/month for TEVIS monitoring, which is dramatically better value. Their existence is reassuring — not threatening.

### What makes this bot defensible

1. TEVIS is city-specific. No national player has incentive to build Düsseldorf-specific scraping.
2. You are already live with real scraping that works. Replicating it requires weeks of engineering.
3. Community trust compounds: once users in Ukrainian/Russian Telegram channels recommend it organically, it spreads without ad spend.

---

## Target Audience

**Primary** (highest conversion probability):
- Ukrainian refugees/immigrants (post-2022) — large wave, need driver's license conversion, Ausländerbehörde follow-ups, registration
- Russian-speaking residents — established community, similar needs
- Both communities are extremely Telegram-native

**Secondary**:
- Turkish community — established, older generation less Telegram-native but 2nd/3rd gen are; Führerschein conversion relevant
- General English-speaking expats — lower density but active online, Reddit/Facebook users
- Students — Anmeldung, driver's license; younger, tech-comfortable

**Services they actually need appointments for** (use these in ad copy, not vague "city services"):
- Führerschein umschreiben (foreign driver's license conversion) — top need for Ukrainians/Russians
- Zulassungsstelle (vehicle registration)
- Ausländerbehörde (residence permit renewals, though this is a separate system)
- Anmeldung alternatives when KVA is backed up
- Standesamt (civil registry)

---

## Free Channels — Post Immediately

These cost nothing except time. Post in the first week.

### Telegram — Ukrainian community

| Channel | Notes | Post format |
|---------|-------|-------------|
| @duesseldorf_ukraina | Düsseldorf Ukrainians, community-run | Personal post, Ukrainian |
| @ukrainci_v_dusseldorfi | Smaller local group | Ukrainian |
| @ukrainci_nimetchyna / similar Germany-wide Ukrainian channels | High reach | Ukrainian |
| @LandNordrheinWestfalen | NRW-focused, multilingual | Ukrainian/RU/EN |
| t.me groups: "Українці в Дюссельдорфі" | Private groups, ask admin | Ukrainian |

### Telegram — Russian-speaking community

| Channel | Notes | Post format |
|---------|-------|-------------|
| @Vmeste_Dusseldorf | Russian-speaking Düsseldorf ("Вместе") | Russian |
| @germany_ru | Large (~50–100k+ subs), Russians in Germany | Russian — ask admin for free post, explain it's a community tool |
| @russlandsdeutsche | Aussiedler community, Germany | Russian/German |
| @nrw_treffpunkt | NRW general | Russian/German |

### Reddit

| Subreddit | Approach | Expected reach |
|-----------|---------|----------------|
| r/germany | Post as "I built a bot to monitor Düsseldorf appointments" — Germans love this | 500k members |
| r/AskGermany | Answer questions about appointment waits with a link | 200k |
| r/ukraine | "для тих хто в Дюссельдорфі" post | 1M+ members |
| r/de | German subreddit | 350k |

Reddit posts by developers about useful tools routinely get 200–2000 upvotes. One good post on r/germany > all paid ads combined in month 1.

### Facebook Groups — Düsseldorf

| Group | Members | Notes |
|-------|---------|-------|
| Expats in Düsseldorf | ~5k | English-speaking, general expat |
| Life in Düsseldorf | ~11k | Active, fast replies |
| Ukrainer in Düsseldorf / similar | Various | Search "Ukrainer Düsseldorf" on Facebook |
| Russischsprachige in Düsseldorf | Various | Search "Russisch Düsseldorf" on Facebook |

### How to write the free post

Don't post a promo. Post a **story**:

> "I got tired of refreshing the TEVIS website every day waiting for a Führerschein conversion appointment. So I built a Telegram bot that does it automatically and pings me when a slot opens. It found me an appointment in 3 days. Free to use: [link]. Works for all Düsseldorf city services."

In Russian: emphasize "бесплатно, без регистрации на сайтах."  
In Ukrainian: emphasize "для тих, хто чекає на конвертацію посвідчення водія."

---

## Paid Channels — €50–100/Month Allocation

### Option A: Direct Telegram channel posts (recommended)

Buy a 1/24 or 2/48 post in relevant channels (1–2 hours pinned, 24–48 hours in feed).

**How to find channels and prices:**

1. Go to [tgstat.com](https://tgstat.com) or [tgstat.ru](https://tgstat.ru)
2. Search for channels: "Дюссельдорф", "Германия украинцы", "NRW Russland"
3. Click "Advertise" on the channel page — most community channels have a price listed
4. Typical prices for community-size channels (5k–50k subs): **€10–60 per post**

**Suggested month-by-month allocation:**

| Month | Channel target | Budget | Expected |
|-------|---------------|--------|---------|
| 1 | 2 Ukrainian Germany channels (e.g. @germany_ru-equivalent + 1 Düsseldorf) | €50 | 100–300 bot starts |
| 2 | Double down on whichever channel worked best + add Russian-speaking NRW | €75 | 200–400 bot starts |
| 3 | Add one Turkish-language community if language support live | €100 | 200–500 bot starts |

**Key rule:** negotiate. Most small-medium Telegram channel admins don't have fixed prices. Offer €15–25 for a 24h post. Many community channels accept this and are grateful someone cares about their audience.

### Option B: Telega.io marketplace

[Telega.io](https://telega.io) is a Telegram advertising exchange. You set a budget, filter by language (Russian, Ukrainian), country (Germany), and buy posts in bulk.

- Minimum spend: ~€20–50 to start
- CPM in relevant channels: ~€3–8 (i.e. €3–8 per 1000 channel members reached)
- For €100: roughly 12,000–30,000 impressions in relevant channels
- Useful for testing multiple channels without negotiating individually

**Verdict:** Good for scale-testing in month 2–3 once you have a working conversion funnel (users join → see value → subscribe).

### Option C: Telegram official Sponsored Messages

**Not viable at this budget.** Minimum via agency: €3,000–5,000 initial deposit. Minimum direct: ~€2M. Skip entirely.

### Option D: Meta (Facebook/Instagram) Ads

Targeting: Düsseldorf + surrounding, languages Russian/Ukrainian, interests "Germany immigration" / "Führerschein".

- CPC in this audience: ~€0.50–2.00
- With €50: 25–100 clicks
- Problem: sends traffic to a landing page or Telegram link. Telegram bots have poor conversion from cold Meta traffic.
- **Verdict:** Low priority. Use only in month 3 if Telegram channels are saturated.

### Option E: Google Ads

Targeting: "Termin Düsseldorf", "Führerschein umschreiben Termin", "TEVIS Düsseldorf".

- CPC for these keywords: €0.50–2.50 in Germany
- With €50: 20–100 clicks
- Search intent is perfect but volume is very low (niche local search)
- **Verdict:** Worth testing €20–30/month in month 2 as a complement. Long-term, organic SEO (a simple landing page) is better.

---

## Recommended Monthly Budget Breakdown

### Month 1 — €60 target

| Channel | Spend | Expected outcome |
|---------|-------|-----------------|
| Free: Reddit r/germany post | €0 | 100–500 clicks if post does well |
| Free: Facebook Düsseldorf groups | €0 | 50–150 organic |
| Paid: 2 Telegram channel posts (Ukrainian community, ~20k total reach) | €40 | 80–200 bot starts |
| Paid: 1 Russian-speaking Germany channel post | €20 | 50–150 bot starts |
| **Total** | **€60** | **250–1000 total bot starts** |

### Month 2 — €80 target

Analyze month 1: which channel → most active users (not just starts). Double down.

| Channel | Spend | Notes |
|---------|-------|-------|
| Best-performing channel from M1, repeat post | €30 | Repeat buyer discount often available |
| Telega.io campaign, RU+UK language filter, Germany | €30 | Test 3–5 smaller channels at once |
| Google Ads experiment | €20 | Keyword: "Termin Düsseldorf bot" |
| **Total** | **€80** | — |

### Month 3 — €100 target

By month 3 you should have real data: conversion rate from free→premium, which services are most popular. If premium conversion > 1%, reinvest. If < 0.5%, rethink the premium offer.

---

## Pricing Strategy for the Bot

The gray market charges €50–100 per single appointment slot. Commercial visa bots charge £35–100/month. Your positioning:

**Recommended pricing (re-enable premium):**
- **FREE tier**: 3 subscriptions, checks every 12 hours. No credit card.
- **PREMIUM**: €2.99/month or €24.99/year (~€2.08/month).
  - Unlimited subscriptions
  - Checks every 1 hour
  - Priority notifications

**Why €2.99 and not €5.99:**
- Your target audience (recent Ukrainian/Russian immigrants) is cost-sensitive
- €2.99 is psychologically a "coffee" purchase, not a subscription
- 100 premium users × €2.99 = €299/month — covers hosting, S3, EC2 and your ad budget with margin
- If conversion is 5% of 2000 users: 100 premium users by month 3

**Upsell path to consider later:**
- One-time "monitor until found" for a single service: €0.99 (captures people who don't want monthly)
- Family pack: €4.99/month for shared account (Führerschein conversions are often done as family)

---

## Key Messages by Audience

**Ukrainian (key service: Führerschein conversion, Ausländerbehörde):**
> Бот для Дюссельдорфа: отримуй сповіщення, коли відкривається запис на перереєстрацію посвідчення водія або інші послуги міста. Безкоштовно. Без черг на сайті.

**Russian-speaking:**
> Бот-уведомитель: как только откроется запись в TEVIS Дюссeldorf — мгновенное сообщение в Telegram. Водительское удостоверение, Anmeldung, Standesamt. Бесплатно.

**English:**
> Never miss a Düsseldorf city appointment again. Get a Telegram notification the instant a slot opens for any TEVIS service. Free tier available.

**German (for Reddit r/germany, local Facebook):**
> Ein Telegram-Bot der automatisch TEVIS Düsseldorf überwacht und benachrichtigt, sobald ein Termin frei wird. Für Führerschein-Umschreibung, Standesamt, Zulassung etc. Kostenlos nutzbar.

---

## Success Metrics — Month by Month

| Metric | Month 1 target | Month 3 target |
|--------|---------------|----------------|
| Total bot users | 200 | 800 |
| Active subscriptions | 150 | 500 |
| Premium users | 5 | 40 |
| Monthly revenue | €15 | €120 |
| CAC (paid users acquired per €) | — | < €2/user |
| Best performing channel | measure | double down |

**Decision gate at month 3:**
- If ≥ 40 premium users (€120 MRR): increase ad budget, MRR covers itself
- If 15–40 premium users: continue €50/month, optimize messaging
- If < 15 premium users: rethink premium offer price or value proposition, not the product

---

## Quick-Start Action List (First Week)

1. **Post on r/germany** — write as a personal story, not a promo. Link to bot. Takes 30 minutes.
2. **Find admins** of @Vmeste_Dusseldorf and @duesseldorf_ukraina — DM them, offer a free post as a community service tool (it genuinely is useful for their members).
3. **Post in 3–4 Facebook groups** — Expats in Düsseldorf, Life in Düsseldorf, Ukrainian group.
4. **Create a tgstat.com account** — browse "Германия украинцы" and "NRW" channels to find ones with 5k–30k members and reasonable post prices before spending anything.
5. **Re-enable premium** — set it to €2.99/month via Telegram Stars (XTR). Even if no one buys immediately, it signals the product has value.

---

*Last updated: 2026-04-19*  
*Phase 2 marketing (paid search landing page, SEO) to be planned once MRR > €200/month.*
