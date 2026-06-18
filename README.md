# Telegram Bot Host - Railway Deployment

Telegram bot for hosting Python/JavaScript files with automatic GitHub backup system.

## 🚀 Quick Start - Railway Deployment

### 1. GitHub Token Banao
```
https://github.com/settings/tokens
→ Generate new token (classic)
→ Select: ✅ repo (Full control)
→ Copy token
```

### 2. Railway Pe Deploy Karo
```
1. Railway.app pe login karo
2. New Project → Deploy from GitHub
3. host-bot repository select karo
```

### 3. Environment Variables Set Karo
```
BACKUP_METHOD=api
GITHUB_TOKEN=your_token_here
GITHUB_REPO=akbhai/host-bot
```

### 4. Done! 🎉
Bot automatically start ho jayega aur har 1 ghante mein backup hoga!

## 📚 Documentation

- **[Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)** - Complete Railway setup guide (Hindi)
- **[Backup System](BACKUP_SYSTEM.md)** - Backup system details

## ✨ Features

- 📤 Upload Python/JavaScript files
- 🚀 Run scripts directly from bot
- 💾 Automatic GitHub backup (every 1 hour)
- 👑 Admin panel with subscription management
- 📊 Statistics and monitoring
- 🔒 Bot lock/unlock functionality

## 🔧 Admin Commands

- `/start` - Main menu
- `/backup` - Manual backup trigger
- `/adminpanel` - Admin management
- `/broadcast` - Send message to all users
- `/lockbot` - Lock/unlock bot

## 📦 Backup System

### Automatic Backup
- **Interval**: Every 1 hour
- **Method**: GitHub API (Railway compatible)
- **Location**: `backups/` folder in repository
- **Format**: `bot_data_YYYYMMDD_HHMMSS.db`

### Manual Backup
- Command: `/backup`
- Admin Panel: "💾 Backup to GitHub" button

## 🛠️ Configuration

Edit in `main.py`:
```python
BACKUP_INTERVAL = 3600  # 1 hour (in seconds)
GITHUB_BACKUP_ENABLED = True
```

## 📊 File Structure

```
host-bot/
├── main.py                    # Main bot script
├── requirements.txt           # Python dependencies
├── runtime.txt               # Python version
├── Procfile                  # Railway start command
├── railway.json              # Railway configuration
├── .env.example              # Environment variables template
├── README.md                 # This file
├── RAILWAY_DEPLOYMENT.md     # Railway deployment guide
├── BACKUP_SYSTEM.md          # Backup system documentation
├── inf/                      # Database folder
│   └── bot_data.db          # SQLite database
├── upload_bots/             # User uploaded files
└── backups/                 # GitHub backups (auto-created)
```

## 🔐 Security

- Never commit `.env` file
- Keep `GITHUB_TOKEN` in Railway environment variables only
- Regularly rotate GitHub tokens
- Use token with minimal required permissions

## 📝 Requirements

- Python 3.10+
- Telegram Bot Token
- GitHub Personal Access Token (for backups)
- Railway account (for hosting)

## 🆘 Support

Issues? Check:
1. Railway logs for errors
2. GitHub token permissions
3. Environment variables configuration

## 📄 License

This project is for personal use.

---

**Made with ❤️ for Railway deployment**
# Railway deployment
