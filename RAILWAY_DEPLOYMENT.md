# Railway Deployment Guide

## 🚂 Railway Pe Bot Deploy Kaise Kare

### Step 1: Railway Pe Project Setup

1. [Railway.app](https://railway.app) pe jao aur login karo
2. **"New Project"** click karo
3. **"Deploy from GitHub repo"** select karo
4. Apna `host-bot` repository select karo
5. Railway automatically detect karega aur deploy karega

### Step 2: Volume Setup (Data Persistence)

**IMPORTANT**: Data persist karne ke liye volume setup karo:

1. Railway Dashboard mein apne project pe jao
2. **"Settings"** tab kholo
3. **"Volumes"** section mein jao
4. **"+ New Volume"** click karo
5. Configure karo:
   - **Mount Path**: `/app/upload_bots`
   - Volume automatically create ho jayega

### Step 3: Deploy Complete!

**Bas itna hi!** Railway automatically:
- ✅ Bot ko deploy karega
- ✅ Data persist rahega (volume mein)
- ✅ Backup system activate karega
- ✅ Telegram pe backup bhejega (Owner ko)

**Koi environment variables set karne ki zarurat NAHI hai!**

## ✅ Backup System Kaise Kaam Karega

### Automatic Backup (Railway pe)

Railway pe bot run hone ke baad:

1. **Har 24 ghante mein** automatic backup hoga
2. **Har user ko apna backup Telegram pe aayega**
3. File name: `backup_USER_ID_YYYYMMDD_HHMMSS.zip`
4. Caption mein stats dikhenge:
   - User ki files count
   - Running/stopped bots status
   - File list

### Manual Backup

User commands:
- `/backup` - Instant backup trigger karo
- "💾 My Backup" button click karo

Admin commands:
- `/backup` - Sabhi users ko backup trigger karo
- Admin Panel → "💾 Backup to GitHub" button

### Backup Files Kaha Milenge?

**Railway pe**: 
- ✅ **Data persist rahega** (Volume mein stored)
- ✅ Deploy/restart ke baad bhi data safe rahega
- Telegram pe har user ko apni file aayegi
- Apne Telegram pe bot se message check karo
- Har 24 ghante mein naya backup file aayega
- ZIP file download karke safe rakho
- Admin ko koi separate backup nahi aayega (sirf users ko)

## 🔧 Configuration Options

### Backup Interval Change Karna

`main.py` mein edit karo:
```python
BACKUP_INTERVAL = 3600  # 1 hour (seconds)
```

Options:
- `1800` = 30 minutes
- `3600` = 1 hour
- `7200` = 2 hours
- `21600` = 6 hours
- `86400` = 24 hours (default)

### Backup Disable Karna

Railway variables mein:
```
GITHUB_BACKUP_ENABLED=False
```

Ya `main.py` mein:
```python
GITHUB_BACKUP_ENABLED = False
```

## 📊 Logs Check Karna

Railway dashboard mein:
1. **"Deployments"** tab pe jao
2. Latest deployment click karo
3. **"View Logs"** click karo

Backup logs dikhenge:
```
🔄 Auto-backup system started (Railway detected - using Telegram to prevent redeploy loop)
📊 Backup method: Telegram (to Owner), Interval: 3600s
Starting Telegram backup...
Found 5 user folders to backup
✅ User 123456789 backup sent via Telegram (3 files)
✅ User 987654321 backup sent via Telegram (5 files)
✅ Backed up 5 user folders, skipped 0 empty folders
```

## 🔍 Troubleshooting

### Backup Nahi Aa Raha Telegram Pe

**Check karo:**
1. Bot start hua hai? (Railway logs dekho)
2. Owner ID sahi hai `main.py` mein?
3. Bot ko block to nahi kiya?

**Logs mein dekho:**
```
✅ Database backup sent to owner via Telegram
```
→ Agar ye dikhe to backup successful hai

```
❌ Telegram Backup error
```
→ Bot token ya owner ID check karo

### Bot Baar Baar Restart Ho Raha Hai

**Ab nahi hoga!** Telegram backup use kar rahe hain, to:
- ✅ No Git commits
- ✅ No GitHub changes
- ✅ No redeploy loop
- ✅ Bot stable rahega

### Backup File Nahi Mil Rahi

1. Telegram pe bot se messages check karo
2. Saved Messages mein dekho
3. File download karke backup rakho

## 🎯 Best Practices

### 1. Token Security
- Token ko kabhi code mein hardcode mat karo
- Sirf Railway environment variables mein rakho
- Token ko regularly rotate karo (har 6 months)

### 2. Backup Monitoring
- Regular logs check karo
- Backup files GitHub pe verify karo
- Agar backup fail ho to turant fix karo

### 3. Storage Management
- Purane backups manually delete kar sakte ho
- Ya GitHub Actions se automatic cleanup setup karo

## 📱 Local Testing (Optional)

Agar local pe test karna hai:

1. `.env` file banao:
```bash
BACKUP_METHOD=git
```

2. Bot run karo:
```bash
python main.py
```

Local pe Git method use hoga, Railway pe API method.

## 🆘 Support

Agar koi problem ho to:
1. Railway logs check karo
2. GitHub token permissions verify karo
3. Repository access check karo

## 📝 Summary

Railway pe deploy karne ke liye:
1. ✅ Railway pe project deploy karo
2. ✅ Volume setup karo (`/app/upload_bots`)
3. ✅ Done! Data persist rahega

**Data Storage**: Railway Volume mein persist rahega
**Backup location**: Telegram pe Owner ko file aayegi (har 24 ghante mein)

## 🎯 Why Telegram Backup?

**Problem**: GitHub backup se Railway redeploy hota tha (infinite loop)
**Solution**: Telegram pe backup bhejte hain
- ✅ No redeploy loop
- ✅ Bot stable rahega
- ✅ Direct file owner ko milegi
- ✅ Easy to download and restore
