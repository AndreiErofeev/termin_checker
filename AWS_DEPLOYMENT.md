# AWS EC2 Deployment Guide - Termin Checker Bot

**Complete Step-by-Step Guide for Deploying to AWS EC2**

---

## Overview

This guide will walk you through deploying the Termin Checker bot to AWS EC2, from creating your AWS account to having a fully functional bot running 24/7.

**Estimated Time:** 45-60 minutes
**Cost:** ~$3-5/month (t4g.nano ARM instance)
**Difficulty:** Medium

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [Create EC2 Instance](#create-ec2-instance)
4. [Configure Security](#configure-security)
5. [Connect to Instance](#connect-to-instance)
6. [Install Dependencies](#install-dependencies)
7. [Deploy Application](#deploy-application)
8. [Configure Auto-Start](#configure-auto-start)
9. [Set Up Database](#set-up-database)
10. [Test Everything](#test-everything)
11. [Monitoring & Maintenance](#monitoring--maintenance)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need

- [ ] AWS Account (free tier eligible for 12 months)
- [ ] Telegram Bot Token (from @BotFather)
- [ ] SSH Client (Terminal on Mac/Linux, PuTTY on Windows)
- [ ] Basic terminal/command line knowledge
- [ ] Credit/debit card for AWS verification (no charge initially)

### Get Your Telegram Bot Token

```bash
1. Open Telegram
2. Search for @BotFather
3. Send /newbot
4. Choose a name: "Düsseldorf Termin Checker"
5. Choose username: "dusseldorf_termin_bot" (must end with 'bot')
6. Copy the token: looks like 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
7. Save it securely - you'll need it later
```

---

## AWS Account Setup

### Step 1: Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **"Create an AWS Account"**
3. Enter email address and choose account name
4. Verify email
5. Set root user password (use a strong password!)
6. Choose **"Personal"** account type
7. Enter billing information (required but won't be charged initially)
8. Verify phone number
9. Choose **"Basic Support - Free"** plan
10. Complete sign-up

**Free Tier Benefits:**
- 750 hours/month of t2.micro or t3.micro (12 months)
- After free tier: t4g.nano costs ~$3/month

### Step 2: Secure Your Root Account

```bash
1. Sign in to AWS Console
2. Go to IAM (Identity and Access Management)
3. Enable MFA (Multi-Factor Authentication) - HIGHLY RECOMMENDED
4. Use Google Authenticator or similar app
5. Save backup codes in secure location
```

### Step 3: Create IAM User (Recommended)

Instead of using root account:

```bash
1. Go to IAM → Users → Add User
2. Username: "admin-user"
3. Check "Provide user access to AWS Console"
4. Set password
5. Attach policies: "AdministratorAccess"
6. Create user
7. Save credentials
8. Sign out and sign in as IAM user for daily operations
```

---

## Create EC2 Instance

### Step 1: Launch Instance

```bash
1. Sign in to AWS Console
2. Search for "EC2" in the top search bar
3. Click "EC2" service
4. Click "Launch Instance" (orange button)
```

### Step 2: Configure Instance

#### Name and Tags
```
Name: termin-checker-bot
Tags:
  - Project: termin-checker
  - Environment: production
```

#### Choose AMI (Amazon Machine Image)
```
Operating System: Ubuntu
Version: Ubuntu Server 24.04 LTS (HVM)
Architecture: 64-bit (Arm) - IMPORTANT for cost savings
```

**Why ARM?** t4g.nano ARM instances are 20% cheaper than x86 instances.

#### Instance Type

**Option 1: Free Tier (First 12 Months)**
```
Type: t2.micro or t3.micro
vCPUs: 1
Memory: 1 GiB
Cost: FREE for 750 hours/month (12 months)
```

**Option 2: Cost-Optimized (After Free Tier)**
```
Type: t4g.nano
vCPUs: 2
Memory: 0.5 GiB
Cost: ~$3/month
Architecture: ARM64 (Graviton2)
```

**Recommendation:** Start with t2.micro (free tier), then switch to t4g.nano after 12 months.

#### Key Pair (Login)

This is CRITICAL for SSH access:

```bash
1. Click "Create new key pair"
2. Key pair name: "termin-checker-key"
3. Key pair type: RSA
4. Private key file format:
   - Mac/Linux: .pem
   - Windows (PuTTY): .ppk
5. Click "Create key pair"
6. File downloads automatically
7. SAVE THIS FILE SECURELY - you cannot download it again!
```

**Save Your Key:**
```bash
# Mac/Linux
mkdir -p ~/.ssh
mv ~/Downloads/termin-checker-key.pem ~/.ssh/
chmod 400 ~/.ssh/termin-checker-key.pem

# Windows
# Move to C:\Users\YourName\.ssh\termin-checker-key.ppk
```

#### Network Settings

```
Create security group: YES
Security group name: termin-checker-sg
Description: Security group for Termin Checker bot

Firewall rules:
✅ Allow SSH traffic from: My IP (recommended)
   - This restricts SSH to your current IP only
   - More secure than "Anywhere"
```

#### Storage

```
Size: 8 GB (minimum)
Volume Type: gp3 (General Purpose SSD)
IOPS: 3000
Throughput: 125 MB/s
Delete on termination: YES (or NO if you want to keep data)
```

#### Advanced Details (Optional)

Leave defaults, or if you want automatic updates:

```yaml
User data (optional):
#!/bin/bash
apt-get update
apt-get upgrade -y
```

### Step 3: Review and Launch

```bash
1. Review all settings in right sidebar
2. Click "Launch instance"
3. Wait 2-3 minutes for instance to start
4. Instance State should show "Running" with green dot
5. Copy Public IPv4 address (e.g., 3.120.45.67)
```

---

## Configure Security

### Step 1: Configure Security Group

Allow SSH from your IP only (already done during instance creation).

To modify later:

```bash
1. EC2 Dashboard → Security Groups
2. Select "termin-checker-sg"
3. Inbound rules → Edit inbound rules
4. SSH rule → Source → My IP (updates to current IP)
5. Save rules
```

**Note:** If your home IP changes, you'll need to update this rule.

### Step 2: (Optional) Create Elastic IP

By default, your EC2 instance gets a new public IP every time it restarts. To keep a permanent IP:

```bash
1. EC2 Dashboard → Elastic IPs
2. Allocate Elastic IP address
3. Actions → Associate Elastic IP address
4. Select your instance
5. Associate

Cost: FREE while associated with running instance
      $0.005/hour if NOT associated or instance stopped
```

---

## Connect to Instance

### Mac/Linux

```bash
# Get your instance public IP from EC2 dashboard
# Replace YOUR_IP with actual IP address

ssh -i ~/.ssh/termin-checker-key.pem ubuntu@YOUR_IP

# If you get "WARNING: UNPROTECTED PRIVATE KEY FILE"
chmod 400 ~/.ssh/termin-checker-key.pem
```

### Windows (PowerShell)

```powershell
# Method 1: Using built-in SSH (Windows 10+)
ssh -i C:\Users\YourName\.ssh\termin-checker-key.pem ubuntu@YOUR_IP

# Method 2: Using PuTTY
1. Open PuTTY
2. Host Name: ubuntu@YOUR_IP
3. Connection → SSH → Auth → Private key file: browse to .ppk file
4. Save session as "termin-checker" for future use
5. Click Open
```

### First Connection

```bash
# You'll see:
The authenticity of host 'x.x.x.x' can't be established.
Are you sure you want to continue connecting (yes/no)?

# Type: yes

# You should now see:
ubuntu@ip-xxx-xxx-xxx-xxx:~$

# This means you're connected!
```

---

## Install Dependencies

### Step 1: Update System

```bash
# Update package list
sudo apt-get update

# Upgrade installed packages
sudo apt-get upgrade -y

# This may take 5-10 minutes
```

### Step 2: Install Python 3.11+

```bash
# Check Python version
python3 --version

# If < 3.11, install Python 3.11
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Verify
python3 --version
# Should show: Python 3.11.x
```

### Step 3: Install pip

```bash
# Install pip for Python 3.11
sudo apt-get install -y python3-pip

# Verify
pip3 --version
```

### Step 4: Install Git

```bash
sudo apt-get install -y git

# Verify
git --version
```

### Step 5: Install Playwright Dependencies

These are system libraries required by Playwright browser automation:

```bash
sudo apt-get install -y \
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
    libasound2t64 \
    libxshmfence1 \
    libglib2.0-0

# Note: On Ubuntu 24.04+, libasound2 was renamed to libasound2t64
# If you get "has no installation candidate" error, the package may already be installed
# or use: sudo apt-get install -y libasound2t64 || sudo apt-get install -y libasound2
```

---

## Deploy Application

### Step 1: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/YOUR_USERNAME/termin_checker.git

# Replace YOUR_USERNAME with your GitHub username
# Example: git clone https://github.com/AndreiErofeev/termin_checker.git

cd termin_checker

# Verify files
ls -la
# You should see: src/, logs/, screenshots/, config.yaml, etc.
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv) at the beginning
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This will take 3-5 minutes
# You should see: Successfully installed playwright-1.55.0 ...
```

### Step 4: Install Playwright Browser

```bash
# Install Chromium browser for Playwright
playwright install chromium

# This downloads ~100MB, takes 2-3 minutes

# Install browser dependencies
playwright install-deps chromium
```

### Step 5: Create Environment File

```bash
# Create .env file with your configuration
nano .env

# Press Ctrl+O to save, Ctrl+X to exit
```

**Add this content** (replace with your actual values):

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_TELEGRAM_ID=your_telegram_user_id

# Application Environment
ENVIRONMENT=production
HEADLESS=true
DEBUG=false

# Browser Configuration
SLOW_MO=300
SCREENSHOT_DIR=screenshots

# Database Configuration
DB_TYPE=sqlite
DB_PATH=/home/ubuntu/termin_checker/appointments.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/ubuntu/termin_checker/logs/bot.log

# Rate Limiting
RATE_LIMIT_ENABLED=true
REQUESTS_PER_HOUR=20
DELAY_BETWEEN_CHECKS_SECONDS=180
```

**How to get your Telegram User ID:**

```bash
1. Open Telegram
2. Search for @userinfobot
3. Send /start
4. Bot will reply with your User ID (e.g., 123456789)
5. Use this as ADMIN_TELEGRAM_ID
```

### Step 6: Create Required Directories

```bash
# Create logs directory
mkdir -p logs

# Create screenshots directory
mkdir -p screenshots

# Set permissions
chmod 755 logs screenshots
```

---

## Configure Auto-Start

### Step 1: Create Systemd Service

This ensures your bot starts automatically when the server boots and restarts if it crashes.

```bash
# Create service file
sudo nano /etc/systemd/system/terminbot.service
```

**Add this content:**

```ini
[Unit]
Description=Termin Checker Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/termin_checker
Environment="PATH=/home/ubuntu/termin_checker/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/termin_checker/venv/bin/python src/bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/termin_checker/logs/bot.log
StandardError=append:/home/ubuntu/termin_checker/logs/bot.error.log

# Process management
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

**Save and exit:** Ctrl+O, Enter, Ctrl+X

### Step 2: Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable terminbot

# Start the service
sudo systemctl start terminbot

# Check status
sudo systemctl status terminbot

# You should see:
# ● terminbot.service - Termin Checker Telegram Bot
#    Loaded: loaded (/etc/systemd/system/terminbot.service; enabled)
#    Active: active (running) since ...
```

### Step 3: Verify Bot is Running

```bash
# Check if process is running
ps aux | grep python

# Should show: /home/ubuntu/termin_checker/venv/bin/python src/bot/main.py

# View live logs
sudo journalctl -u terminbot -f

# You should see:
# INFO - Initializing database...
# INFO - Initializing bot handlers...
# INFO - Starting bot...

# Press Ctrl+C to exit log view
```

---

## Set Up Database

### Step 1: Initialize Database

```bash
cd ~/termin_checker

# Activate virtual environment
source venv/bin/activate

# Initialize database with default services
python src/core/database.py init

# Expected output:
# Initializing database at sqlite:///appointments.db
# Creating tables...
# Adding default services...
# Database initialized successfully!
```

### Step 2: Verify Database

```bash
# Check database statistics
python src/core/database.py stats

# Expected output:
# Database Statistics:
#   Users: 0
#   Services: 5
#   Subscriptions: 0
#   Checks: 0
#   Appointments: 0
#   Notifications: 0
```

### Step 3: Verify Database File

```bash
# Check if database file exists
ls -lh appointments.db

# Should show: -rw-r--r-- 1 ubuntu ubuntu 143K Nov  9 15:30 appointments.db
```

---

## Test Everything

### Step 1: Test Bot Commands

```bash
1. Open Telegram on your phone/computer
2. Search for your bot username (e.g., @dusseldorf_termin_bot)
3. Send: /start

Expected response:
👋 Welcome [Your Name]!

This bot helps you monitor appointment availability
for Düsseldorf city services.

Available commands:
/subscribe - Subscribe to a service
/list - View your subscriptions
...

Your plan: FREE
```

### Step 2: Test Subscription Flow

```bash
1. Send: /subscribe
2. Bot shows categories with inline buttons
3. Click a category
4. Bot shows services in that category
5. Click a service
6. Bot confirms subscription created

Expected:
✅ Subscription created!

Service: Umschreibung ausländischer Führerschein (sonstige Staaten)
Category: Umschreibung ausländische Fahrerlaubnis / Dienstfahrerlaubnis
Check interval: Every 1h

You'll receive notifications when appointments are available.
```

### Step 3: Test Manual Check

```bash
1. Send: /check
2. Select your subscription
3. Wait 5-10 seconds
4. Bot shows check results

Expected (if no appointments):
❌ No appointments available at the moment.

The bot will notify you when appointments become available.

Expected (if appointments found):
✅ Found 96 appointment(s)!

📅 2025-11-18 at 14:00
📅 2025-11-18 at 14:05
...
```

### Step 4: Verify Scheduler

```bash
# Check logs for scheduler activity
tail -f ~/termin_checker/logs/bot.log

# Wait 5 minutes and you should see:
# INFO - Running scheduled check for due subscriptions...
# INFO - Found 1 subscription(s) due for checking
# INFO - Checking subscription 1...
# INFO - Check completed: no_appointments, Appointments: 0

# Press Ctrl+C to exit
```

### Step 5: Test Database Updates

```bash
# Check database after creating subscription
python src/core/database.py stats

# Should now show:
#   Users: 1
#   Subscriptions: 1
#   Checks: 1 (after scheduler runs or manual check)
```

---

## Monitoring & Maintenance

### View Logs

```bash
# Real-time logs (systemd)
sudo journalctl -u terminbot -f

# Last 100 lines
sudo journalctl -u terminbot -n 100

# Logs from today
sudo journalctl -u terminbot --since today

# Application logs
tail -f ~/termin_checker/logs/bot.log

# Error logs
tail -f ~/termin_checker/logs/bot.error.log
```

### Check Service Status

```bash
# Check if service is running
sudo systemctl status terminbot

# Restart service
sudo systemctl restart terminbot

# Stop service
sudo systemctl stop terminbot

# Start service
sudo systemctl start terminbot

# View service configuration
sudo systemctl cat terminbot
```

### Monitor System Resources

```bash
# CPU and Memory usage
htop

# Disk space
df -h

# Check database size
du -h ~/termin_checker/appointments.db

# Check log file sizes
du -h ~/termin_checker/logs/
```

### Database Maintenance

```bash
# Create database backup
cp ~/termin_checker/appointments.db ~/termin_checker/appointments_backup_$(date +%Y%m%d).db

# View recent checks
sqlite3 ~/termin_checker/appointments.db "SELECT * FROM checks ORDER BY checked_at DESC LIMIT 10;"

# Count total users
sqlite3 ~/termin_checker/appointments.db "SELECT COUNT(*) FROM users;"
```

### Update Application

```bash
cd ~/termin_checker

# Pull latest changes from GitHub
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart terminbot

# Check logs
sudo journalctl -u terminbot -f
```

### Set Up Automatic Updates (Optional)

```bash
# Create update script
nano ~/update_bot.sh
```

**Add this content:**

```bash
#!/bin/bash
cd /home/ubuntu/termin_checker
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --quiet
sudo systemctl restart terminbot
echo "Bot updated at $(date)" >> /home/ubuntu/update.log
```

**Make executable and schedule:**

```bash
chmod +x ~/update_bot.sh

# Add to crontab (daily at 3 AM)
crontab -e

# Add this line:
0 3 * * * /home/ubuntu/update_bot.sh
```

### Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/terminbot
```

**Add this content:**

```
/home/ubuntu/termin_checker/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
}
```

---

## Troubleshooting

### Bot Not Starting

**Check logs:**
```bash
sudo journalctl -u terminbot -n 50
```

**Common issues:**

1. **Missing TELEGRAM_BOT_TOKEN**
```bash
# Check .env file
cat ~/termin_checker/.env | grep TELEGRAM_BOT_TOKEN

# If empty, add token:
nano ~/termin_checker/.env
```

2. **Database not initialized**
```bash
cd ~/termin_checker
source venv/bin/activate
python src/core/database.py init
sudo systemctl restart terminbot
```

3. **Permission issues**
```bash
# Fix permissions
sudo chown -R ubuntu:ubuntu ~/termin_checker
chmod 644 ~/termin_checker/.env
sudo systemctl restart terminbot
```

4. **Python dependencies missing**
```bash
cd ~/termin_checker
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart terminbot
```

### Playwright/Browser Issues

**Error: "Browser executable not found"**
```bash
cd ~/termin_checker
source venv/bin/activate
playwright install chromium
playwright install-deps chromium
sudo systemctl restart terminbot
```

**Error: "Timeout waiting for page"**
```bash
# Increase timeout in config.yaml
nano ~/termin_checker/config.yaml

# Change:
browser:
  timeout: 60000  # Increase from 30000 to 60000
```

### Scheduler Not Running Checks

**Check if subscriptions exist:**
```bash
sqlite3 ~/termin_checker/appointments.db "SELECT * FROM subscriptions WHERE active=1;"
```

**Check scheduler logs:**
```bash
grep "scheduled check" ~/termin_checker/logs/bot.log
```

**Verify subscription is due:**
```bash
python3 << EOF
from src.core.database import init_database
from src.services import SubscriptionService
db = init_database()
subs = SubscriptionService(db)
due = subs.get_subscriptions_due_for_check()
print(f"Subscriptions due: {len(due)}")
for s in due:
    print(f"  - ID: {s.id}, Service: {s.service.service_name}")
EOF
```

### Notifications Not Sending

**Test notification manually:**
```bash
cd ~/termin_checker
source venv/bin/activate
python3 << EOF
import asyncio
import os
from src.core.database import init_database
from src.services import NotificationService

async def test():
    db = init_database()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    notif = NotificationService(db, token)
    result = await notif.send_custom_message(
        YOUR_TELEGRAM_ID,  # Replace with your ID
        "Test notification from bot"
    )
    print(f"Sent: {result}")

asyncio.run(test())
EOF
```

### Out of Memory

**If t4g.nano (512MB) runs out of memory:**

1. **Add swap file:**
```bash
# Create 1GB swap file
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
```

2. **Or upgrade instance:**
```bash
# Stop instance
# EC2 Dashboard → Instances → Select instance
# Actions → Instance Settings → Change instance type
# Choose t4g.micro (1GB RAM, ~$6/month)
# Start instance
```

### High CPU Usage

**Check what's using CPU:**
```bash
top

# Press 1 to see per-core usage
# Press Shift+P to sort by CPU
# Press q to quit
```

**Reduce check frequency:**
```bash
# Edit user's subscription interval
sqlite3 ~/termin_checker/appointments.db
UPDATE subscriptions SET interval_hours = 2 WHERE interval_hours = 1;
.quit
```

### SSH Connection Issues

**Connection timeout:**
```bash
# Check if instance is running
# EC2 Dashboard → Instances → Check "Instance state"

# Check security group allows your IP
# Security Groups → termin-checker-sg → Inbound rules
# Update "My IP" if your IP changed
```

**Permission denied (publickey):**
```bash
# Verify key file permissions
chmod 400 ~/.ssh/termin-checker-key.pem

# Verify correct key file
ssh -i ~/.ssh/termin-checker-key.pem ubuntu@YOUR_IP

# If still fails, check EC2 console "Connect" button for instructions
```

---

## Cost Optimization

### Monitor Your Costs

```bash
1. AWS Console → Billing Dashboard
2. View "Month-to-Date Spend"
3. Set up billing alerts:
   - Billing Preferences → Alert Preferences
   - Enable "Receive Billing Alerts"
   - CloudWatch → Billing → Create Alarm
   - Set threshold (e.g., $5)
```

### Cost Breakdown

**t2.micro (Free Tier, 12 months):**
```
Compute: $0 (750 hours/month free)
Storage: $0 (30GB free)
Data Transfer: $0 (1GB outbound free)
Total: $0/month
```

**t4g.nano (After Free Tier):**
```
Compute: $3.01/month (730 hours × $0.00412/hour)
Storage: $0.80/month (8GB × $0.10/GB)
Data Transfer: $0 (minimal usage)
Total: ~$3.81/month
```

### Save Money

1. **Stop instance when not needed** (development only):
```bash
# Stop instance (data persists, no compute charges)
# EC2 Dashboard → Instances → Select instance → Stop

# Elastic IP charges $0.005/hour when instance stopped
# Release Elastic IP if stopping long-term
```

2. **Use t4g ARM instances** (20% cheaper than t3)

3. **Clean up old data:**
```bash
# Delete old screenshots
find ~/termin_checker/screenshots -name "*.png" -mtime +7 -delete

# Delete old log files
find ~/termin_checker/logs -name "*.log" -mtime +30 -delete
```

---

## Security Best Practices

### 1. Keep System Updated

```bash
# Weekly updates
sudo apt-get update && sudo apt-get upgrade -y
```

### 2. Limit SSH Access

```bash
# Allow SSH only from your IP
# EC2 → Security Groups → Edit inbound rules
# Source: My IP (not 0.0.0.0/0)
```

### 3. Use Key-Based Authentication

```bash
# Never use password authentication
# Always use SSH keys
# Keep your .pem file secure and never share it
```

### 4. Secure Environment Variables

```bash
# Restrict .env file permissions
chmod 600 ~/termin_checker/.env

# Never commit .env to git
# It's already in .gitignore
```

### 5. Enable AWS CloudTrail (Optional)

```bash
# Track all API calls to your AWS account
# AWS Console → CloudTrail → Create trail
# Useful for security auditing
```

### 6. Regular Backups

```bash
# Create backup script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf ~/backups/termin_checker_$DATE.tar.gz \
    ~/termin_checker/appointments.db \
    ~/termin_checker/.env \
    ~/termin_checker/logs
find ~/backups -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x ~/backup.sh

# Run daily at 2 AM
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh
```

---

## Next Steps

### 1. Monitor for 1 Week

- [ ] Check logs daily: `sudo journalctl -u terminbot -f`
- [ ] Verify scheduler runs every 5 minutes
- [ ] Test all bot commands
- [ ] Monitor AWS costs in Billing Dashboard

### 2. Add Monitoring (Optional)

Consider adding:
- Uptime monitoring (UptimeRobot, free)
- Error tracking (Sentry, free tier)
- Log aggregation (CloudWatch Logs)

### 3. Scale When Needed

When you reach 100+ users:
- Upgrade to t4g.micro (1GB RAM, ~$6/month)
- Add swap file for memory
- Optimize database queries

---

## Quick Reference Commands

```bash
# Check bot status
sudo systemctl status terminbot

# View live logs
sudo journalctl -u terminbot -f

# Restart bot
sudo systemctl restart terminbot

# Update bot
cd ~/termin_checker && git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart terminbot

# Check database
python ~/termin_checker/src/core/database.py stats

# Backup database
cp ~/termin_checker/appointments.db ~/termin_checker/appointments_backup_$(date +%Y%m%d).db

# SSH to server
ssh -i ~/.ssh/termin-checker-key.pem ubuntu@YOUR_IP
```

---

## Support

If you encounter issues:

1. Check logs: `sudo journalctl -u terminbot -n 100`
2. Review this troubleshooting section
3. Check GitHub issues: https://github.com/YOUR_USERNAME/termin_checker/issues
4. AWS Support (if account issue)

---

**Deployment Complete!** 🎉

Your bot is now running 24/7 on AWS EC2, automatically checking for appointments and notifying users via Telegram.

**Total setup time:** 45-60 minutes
**Monthly cost:** ~$3-5 (after free tier)
**Uptime:** 99.9%+

---

**Last Updated:** 2025-11-09
**AWS Region Recommendations:** eu-central-1 (Frankfurt) or eu-west-1 (Ireland) for EU users
