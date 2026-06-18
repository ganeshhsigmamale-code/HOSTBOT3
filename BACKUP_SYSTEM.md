# Automatic GitHub Backup System

## Overview
Bot automatically backs up all user data to GitHub repository at regular intervals.

## 🚂 Railway Deployment
**Railway pe deploy kar rahe ho?** Complete guide dekho: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

## Features

### 1. Automatic Backups
- **Interval**: Every 1 hour (3600 seconds)
- **Data Backed Up**:
  - `inf/bot_data.db` - SQLite database containing:
    - User subscriptions
    - User files metadata
    - Active users list
    - Admin IDs
  - `upload_bots/` - All user uploaded files and scripts

### 2. Manual Backup
Admins can trigger manual backups using:
- **Command**: `/backup`
- **Admin Panel**: Click "💾 Backup to GitHub" button

### 3. Configuration

In `main.py`:
```python
# Backup Configuration
BACKUP_INTERVAL = 3600  # Backup every 1 hour (in seconds)
GITHUB_BACKUP_ENABLED = True  # Set to False to disable auto-backup
```

## How It Works

1. **Automatic Mode**:
   - Background thread runs continuously
   - Every hour, checks for changes in data files
   - If changes detected, commits and pushes to GitHub
   - Commit message format: `Auto-backup: YYYY-MM-DD HH:MM:SS`

2. **Manual Mode**:
   - Admin triggers backup via command or button
   - Immediately checks and commits any changes
   - Provides feedback on success/failure

3. **Git Operations**:
   - Checks for changes: `git status --porcelain`
   - Adds data directories: `git add inf/ upload_bots/`
   - Creates commit with timestamp
   - Pushes to origin: `git push origin HEAD`

## Requirements

- Git repository must be initialized
- Git credentials must be configured (for push access)
- Bot must have write permissions to repository

## Logs

All backup operations are logged:
- ✅ Successful backups
- ❌ Failed operations
- ℹ️ No changes detected

Check logs for backup status and troubleshooting.

## Disabling Backups

To disable automatic backups, set in `main.py`:
```python
GITHUB_BACKUP_ENABLED = False
```

Manual backups via `/backup` command will still work.

## Customization

### Change Backup Interval
Modify `BACKUP_INTERVAL` in seconds:
```python
BACKUP_INTERVAL = 1800  # 30 minutes
BACKUP_INTERVAL = 7200  # 2 hours
BACKUP_INTERVAL = 86400  # 24 hours
```

### Backup Additional Files
Add more directories in `backup_to_github()` function:
```python
subprocess.run(['git', 'add', 'your_directory/'], cwd=BASE_DIR, check=False)
```

## Troubleshooting

### Backup Not Working
1. Check if `GITHUB_BACKUP_ENABLED = True`
2. Verify Git credentials are configured
3. Check logs for error messages
4. Ensure bot has write access to repository

### Push Failures
- Verify GitHub authentication
- Check network connectivity
- Ensure no merge conflicts
- Review Git remote configuration

### No Changes Detected
- Normal if no user activity
- Database and files only backed up when modified
- Check logs to confirm backup system is running
