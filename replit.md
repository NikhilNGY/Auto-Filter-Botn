# Auto Filter Bot - Telegram Bot

## Overview
This is a Telegram Auto Filter Bot built with Python using the Hydrogram library. The bot provides automatic file filtering, IMDB integration, user management, and includes a minimal web interface for health checks.

**Current Status**: ✅ Setup complete - Ready for configuration

## Recent Changes
- **2024-09-19**: Project imported and set up for Replit environment
  - Installed Python 3.11 and all required dependencies
  - Configured MongoDB database (local instance running on port 27017)
  - Set up workflow to run on port 5000 with webview output
  - Fixed port configuration from 8080 to 5000 for Replit compatibility
  - Added proper web_app import to resolve import issues

## Project Architecture

### Backend Components
- **Telegram Bot**: Uses Hydrogram library for Telegram API interaction
- **Web Server**: Flask-based health check endpoint on port 5000
- **Database**: MongoDB for storing files, users, groups, and settings
- **File Management**: Handles file indexing, searching, and filtering

### Key Features
- Automatic file filtering and search
- IMDB movie information integration
- User and group management
- Force subscription support
- Settings management per group
- Broadcast functionality
- File protection and security
- Verification system
- Shortlink support

### File Structure
```
├── bot.py              # Main bot entry point
├── info.py             # Configuration and environment variables
├── utils.py            # Utility functions and temp storage
├── Script.py           # Bot text templates and messages
├── web/
│   └── app.py          # Flask web application for health checks
├── database/
│   ├── users_chats_db.py   # Database operations
│   └── ia_filterdb.py      # File filtering database
├── plugins/            # Bot command handlers
│   ├── commands.py     # Admin and user commands
│   ├── pm_filter.py    # Private message filtering
│   ├── inline.py       # Inline query handling
│   └── [other plugins]
└── requirements.txt    # Python dependencies
```

## Environment Configuration

### Required Environment Variables

**Essential Telegram Configuration:**
- `API_ID`: Telegram API ID from https://my.telegram.org/apps
- `API_HASH`: Telegram API Hash from https://my.telegram.org/apps  
- `BOT_TOKEN`: Bot token from @BotFather on Telegram
- `ADMINS`: Space-separated admin user IDs
- `LOG_CHANNEL`: Channel ID for bot logs (bot must be admin)

**Database Configuration:**
- `DATA_DATABASE_URL`: MongoDB URL for user/group data (default: mongodb://localhost:27017)
- `FILES_DATABASE_URL`: MongoDB URL for file storage (default: mongodb://localhost:27017)
- `SECOND_FILES_DATABASE_URL`: Optional second database URL
- `DATABASE_NAME`: Database name (default: Autof1)

**Channel Configuration:**
- `SUPPORT_GROUP`: Support group ID
- `BIN_CHANNEL`: Channel for file streaming (bot must be admin)
- `INDEX_CHANNELS`: Space-separated channel IDs to index files from
- `AUTH_CHANNEL`: Force subscribe channel IDs

### Optional Configuration
- `PORT`: Server port (configured for 5000)
- `SHORTLINK_URL`: URL shortening service
- `SHORTLINK_API`: API key for shortening service
- `FILE_CAPTION`: Custom file caption template
- `WELCOME_TEXT`: Welcome message template
- `VERIFY_EXPIRE`: Verification expiry time in seconds

## Setup Instructions

### 1. MongoDB Database
✅ **Status**: Configured and running
- Local MongoDB instance running on port 27017
- Database path: `/tmp/mongodb_data`
- Logs: `/tmp/mongodb.log`

### 2. Environment Variables Setup
**To run this bot, you need to configure the following in Replit Secrets:**

1. Go to the "Secrets" tab in your Replit workspace
2. Add the required variables:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   LOG_CHANNEL=your_log_channel_id
   ADMINS=your_admin_id
   SUPPORT_GROUP=your_support_group_id
   BIN_CHANNEL=your_bin_channel_id
   ```

### 3. Telegram Bot Setup
1. Create a bot via @BotFather on Telegram
2. Get API credentials from https://my.telegram.org/apps
3. Create required channels and add the bot as admin
4. Configure channel IDs in environment variables

### 4. Workflow Configuration
✅ **Status**: Configured
- Workflow name: "Bot"
- Command: `python3 bot.py`
- Port: 5000 (webview output)
- Auto-restart enabled

## User Preferences
- **Environment**: Replit cloud environment
- **Database**: MongoDB (local instance)
- **Port Configuration**: 5000 for web interface
- **Output Type**: Webview for web interface access

## Current Status
The bot is properly configured for the Replit environment with all dependencies installed and the database running. To complete setup:

1. **Add Telegram credentials** to Replit Secrets
2. **Create and configure Telegram channels** (log, support, bin channels)  
3. **Start the workflow** - it will automatically run when environment variables are set

## Commands Reference
See README.md for complete command list. Key admin commands:
- `/start` - Check bot status
- `/stats` - Get bot statistics  
- `/settings` - Group settings management
- `/broadcast` - Send messages to all users
- `/index` - Index files from channels

## Deployment
The project is configured for deployment with:
- **Development**: Replit environment with local MongoDB
- **Production**: Ready for cloud deployment (see deployment configuration)

## Notes
- The bot requires proper Telegram channel setup for full functionality
- File indexing requires channels where the bot has admin access
- All sensitive credentials should be stored in Replit Secrets
- MongoDB data is stored locally in development environment