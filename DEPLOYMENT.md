# Deployment Guide - Termin Checker Bot

**Last Updated:** 2025-11-09
**Status:** Production-ready with critical fixes applied

---

## Pre-Deployment Checklist

### Critical Fixes Applied ✅
- [x] Fixed `user.last_activity` attribute mismatch
- [x] Fixed `subscription.last_checked_at` attribute mismatch
- [x] Fixed `service.last_appointments_at` attribute mismatch
- [x] Added missing `notify_telegram` field to Subscription model
- [x] Created `logs/` directory
- [x] Integrated NotificationService with SchedulerService
- [x] Installed testing dependencies (pytest, pytest-asyncio)

### Requirements
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- ~100MB disk space (SQLite)
- 512MB-1GB RAM minimum

---

## Deployment Option 1: Railway.app (RECOMMENDED for Pet Projects)

**Cost:** $0-5/month | **Difficulty:** Easy | **Setup Time:** 15 minutes

### Why Railway?
- Free tier with 500 hours/month
- Automatic deployments from GitHub
- Simple environment variable management
- No credit card required for free tier
- Can upgrade to $5/month Starter plan when needed

### Step-by-Step Deployment

#### 1. Prepare Your Bot

```bash
# Get your bot token from @BotFather
# 1. Open Telegram and search for @BotFather
# 2. Send /newbot
# 3. Follow prompts to create bot
# 4. Copy the token

# Your token looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

#### 2. Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (easiest)
3. Authorize Railway to access your repository

#### 3. Deploy from GitHub

```bash
# In Railway dashboard:
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose "termin_checker" repository
4. Railway auto-detects Python and deploys
```

#### 4. Configure Environment Variables

In Railway project settings → Variables:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional
ADMIN_TELEGRAM_ID=your_telegram_user_id
LOG_LEVEL=INFO
DB_PATH=/app/data/appointments.db
HEADLESS=true
```

#### 5. Add Persistent Storage (Optional)

```bash
# In Railway project:
1. Go to Settings → Volumes
2. Add volume: /app/data
3. This persists your SQLite database across deploys
```

#### 6. Start the Bot

Railway automatically runs:
```bash
python src/bot/main.py
```

If custom start command needed, add `Procfile`:
```
web: python src/bot/main.py
```

#### 7. Monitor Logs

```bash
# In Railway dashboard:
# Go to Deployments → View Logs
# You should see:
# INFO - Initializing database...
# INFO - Starting bot...
```

#### 8. Test Your Bot

1. Open Telegram
2. Search for your bot username
3. Send `/start`
4. Should receive welcome message

---

## Deployment Option 2: DigitalOcean Droplet

**Cost:** $4-6/month | **Difficulty:** Medium | **Setup Time:** 30 minutes

### Step-by-Step Deployment

#### 1. Create Droplet

```bash
# DigitalOcean → Create Droplet
# - Image: Ubuntu 24.04 LTS
# - Plan: Basic - $4/mo (512MB RAM)
# - Datacenter: Closest to you
# - Authentication: SSH key
```

#### 2. Initial Server Setup

```bash
# SSH into your droplet
ssh root@your_droplet_ip

# Update system
apt update && apt upgrade -y

# Install Python 3.11+
apt install python3 python3-pip python3-venv git -y

# Install Playwright dependencies
apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

#### 3. Deploy Application

```bash
# Create app user
useradd -m -s /bin/bash terminbot
su - terminbot

# Clone repository
git clone https://github.com/YOUR_USERNAME/termin_checker.git
cd termin_checker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create environment file
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_ID=your_telegram_id
LOG_LEVEL=INFO
HEADLESS=true
EOF

# Initialize database
python src/core/database.py init
```

#### 4. Create Systemd Service

```bash
# Exit terminbot user
exit

# Create service file
cat > /etc/systemd/system/terminbot.service << 'EOF'
[Unit]
Description=Termin Checker Telegram Bot
After=network.target

[Service]
Type=simple
User=terminbot
WorkingDirectory=/home/terminbot/termin_checker
Environment="PATH=/home/terminbot/termin_checker/venv/bin"
ExecStart=/home/terminbot/termin_checker/venv/bin/python src/bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable terminbot
systemctl start terminbot

# Check status
systemctl status terminbot

# View logs
journalctl -u terminbot -f
```

#### 5. Set Up Auto-Update (Optional)

```bash
# Create update script
cat > /home/terminbot/update.sh << 'EOF'
#!/bin/bash
cd /home/terminbot/termin_checker
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart terminbot
EOF

chmod +x /home/terminbot/update.sh

# Add to cron for daily updates (optional)
crontab -e -u terminbot
# Add: 0 3 * * * /home/terminbot/update.sh
```

---

## Deployment Option 3: Fly.io

**Cost:** $0 (free tier) | **Difficulty:** Medium | **Setup Time:** 20 minutes

### Step-by-Step Deployment

#### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

#### 2. Create Dockerfile

```dockerfile
# Create Dockerfile in project root
FROM python:3.11-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p logs

# Initialize database
RUN python src/core/database.py init

# Run bot
CMD ["python", "src/bot/main.py"]
```

#### 3. Create fly.toml

```toml
app = "termin-checker-bot"
primary_region = "fra"  # Frankfurt, or choose nearest

[build]
  dockerfile = "Dockerfile"

[env]
  HEADLESS = "true"
  LOG_LEVEL = "INFO"

[mounts]
  source = "termin_data"
  destination = "/app/data"
```

#### 4. Deploy

```bash
# Login to Fly
flyctl auth login

# Launch app (interactive setup)
flyctl launch

# Set secrets
flyctl secrets set TELEGRAM_BOT_TOKEN=your_token_here
flyctl secrets set ADMIN_TELEGRAM_ID=your_id

# Deploy
flyctl deploy

# Check status
flyctl status

# View logs
flyctl logs
```

---

## Post-Deployment Steps

### 1. Verify Bot is Running

```bash
# Test commands in Telegram:
/start      # Should receive welcome message
/help       # Should show command list
/subscribe  # Should show service categories
```

### 2. Monitor Logs

**Railway:**
```
Dashboard → Deployments → View Logs
```

**DigitalOcean:**
```bash
journalctl -u terminbot -f
```

**Fly.io:**
```bash
flyctl logs
```

### 3. Check Database

```bash
# SSH into server or use Railway shell
python src/core/database.py stats

# Expected output:
# Database Statistics:
#   Users: 1 (after /start)
#   Services: 5
#   Subscriptions: 0 (after /subscribe)
#   Checks: 0
```

### 4. Test Scheduler

```bash
# The scheduler should log every 5 minutes:
# "Running scheduled check for due subscriptions..."
# "No subscriptions due for checking" (if no subscriptions yet)
```

### 5. Test Full Flow

1. User sends `/start`
2. User sends `/subscribe`
3. Select category and service
4. Wait for scheduler to run (max 5 minutes)
5. Check logs for appointment check execution

---

## Monitoring & Maintenance

### Health Checks

Create a simple health check endpoint (future enhancement):

```python
# In src/bot/main.py, add:
from datetime import datetime

# Store last check time
last_health_check = datetime.now()

# Update in scheduler
def update_health():
    global last_health_check
    last_health_check = datetime.now()
```

### Log Rotation

**DigitalOcean:**
```bash
# /etc/logrotate.d/terminbot
/home/terminbot/termin_checker/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### Database Backup

```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp appointments.db backups/appointments_$DATE.db
find backups/ -name "appointments_*.db" -mtime +7 -delete
```

### Monitoring Alerts

Set up alerts for:
- Bot crashes (automatic with Railway/Fly.io)
- Database errors (check logs)
- Failed appointment checks (> 50% failure rate)

---

## Scaling Considerations

### Current Capacity
- **SQLite:** Suitable for <1000 users
- **Scheduler:** Single process, sequential checks
- **Bot:** Polling mode, suitable for <1000 users

### When to Scale

**At 100+ users:**
- Switch to webhook mode (faster)
- Add database indexes for common queries
- Implement check result caching

**At 1000+ users:**
- Migrate to PostgreSQL
- Use separate scheduler process
- Implement rate limiting
- Add Redis for caching

**At 10,000+ users:**
- Kubernetes deployment
- Read replicas for database
- Distributed task queue (Celery)
- CDN for screenshots

---

## Troubleshooting

### Bot Not Starting

```bash
# Check logs for error
# Common issues:
1. Missing TELEGRAM_BOT_TOKEN
2. Invalid bot token
3. Database not initialized
4. Missing logs/ directory

# Fix:
python src/core/database.py init
mkdir -p logs
```

### Scheduler Not Running Checks

```bash
# Check:
1. Subscription exists and is active
2. last_checked_at is None or >interval_hours ago
3. User has notify_telegram=true

# Debug:
python -c "from src.core.database import init_database; from src.services import SubscriptionService; db = init_database(); s = SubscriptionService(db); print(s.get_subscriptions_due_for_check())"
```

### Notifications Not Sending

```bash
# Check:
1. TELEGRAM_BOT_TOKEN is set
2. NotificationService initialized in scheduler
3. subscription.notify_telegram is True
4. subscription.notify_on_found is True

# Test manually:
python -c "import asyncio; from src.core.database import init_database; from src.services import NotificationService; import os; db = init_database(); n = NotificationService(db, os.getenv('TELEGRAM_BOT_TOKEN')); asyncio.run(n.send_custom_message(YOUR_TELEGRAM_ID, 'Test message'))"
```

### Database Locked Errors

```bash
# SQLite doesn't handle high concurrency well
# Solutions:
1. Ensure one scheduler instance only
2. Reduce check frequency
3. Migrate to PostgreSQL
```

---

## Cost Comparison

| Platform | Monthly Cost | Setup Difficulty | Best For |
|----------|-------------|------------------|----------|
| Railway.app | $0-5 | Easy | Pet projects, testing |
| DigitalOcean | $4-6 | Medium | Full control, multiple projects |
| Fly.io | $0-3 | Medium | Modern deployment, free tier |
| AWS EC2 | $0-5 | Hard | Enterprise, existing AWS |
| Heroku | $7+ | Easy | Simplicity, no free tier |

---

## Recommended Path for Pet Project

1. **Start:** Railway.app free tier
2. **Test:** Full functionality for 1 week
3. **Monitor:** Check logs, test all commands
4. **Decide:**
   - Staying small? Keep Railway ($0-5/mo)
   - Want control? Move to DigitalOcean ($4/mo)
   - Need scale? Upgrade Railway or AWS

---

## Quick Deploy Commands

### Railway.app
```bash
# One-time setup
railway login
railway link
railway up

# Set secrets
railway variables set TELEGRAM_BOT_TOKEN=your_token
```

### DigitalOcean
```bash
# One-line install
ssh root@your_ip "curl -fsSL https://github.com/YOUR_USERNAME/termin_checker/raw/main/deploy.sh | bash"
```

### Fly.io
```bash
flyctl launch
flyctl secrets set TELEGRAM_BOT_TOKEN=your_token
flyctl deploy
```

---

## Next Steps After Deployment

1. ✅ Monitor for 1 week
2. ✅ Test all bot commands
3. ✅ Verify scheduler runs every 5 minutes
4. ✅ Check notification delivery
5. ⏳ Add unit tests (see TESTING.md)
6. ⏳ Set up CI/CD (see .github/workflows/)
7. ⏳ Add monitoring (Sentry, Prometheus)

---

**Questions?** Check [PHASE3_SUMMARY.md](PHASE3_SUMMARY.md) for implementation details or open an issue on GitHub.
