# Telegram File Link Bot

## Overview
A Python-based Telegram bot that generates shareable deep-links for files and media forwarded from Telegram channels. The bot uses SQLite for persistence and automatically cleans up expired links.

**Bot Username:** smxfilesbot

## Recent Changes
- **2025-11-17:** Initial project setup
  - Created bot.py with full functionality
  - Set up SQLite database with token management
  - Implemented forwarded message detection and deep-link generation
  - Added automatic cleanup task (runs hourly)
  - Created comprehensive README with setup instructions

## Project Architecture

### Core Files
- **bot.py**: Main bot application with all handlers and database operations
- **requirements.txt**: Python dependencies (python-telegram-bot, aiosqlite, python-dotenv)
- **file_links.db**: SQLite database (auto-created on first run)
- **README.md**: Complete documentation and setup guide

### Database Schema
```sql
file_links:
  - token (TEXT, PRIMARY KEY)
  - from_chat_id (INTEGER)
  - from_message_id (INTEGER)
  - created_at (TEXT, ISO format)
  - max_uses (INTEGER, default 0 = unlimited)
  - uses (INTEGER, default 0)
```

### Key Features
1. Forwarded message detection from channels
2. Unique token generation (cryptographically secure)
3. Deep-link creation: `https://t.me/smxfilesbot?start=<token>`
4. Message copying without "Forwarded from..." attribution
5. Automatic cleanup of tokens older than 7 days
6. Usage tracking and validation

### Environment Variables
- **BOT_TOKEN** (required): Telegram Bot API token from @BotFather
- **BOT_USERNAME** (default: smxfilesbot): Bot username for deep-link generation
- **TOKEN_TTL_DAYS** (default: 7): Number of days before links expire

## Technical Stack
- Python 3.11
- python-telegram-bot v20.7 (async/await)
- aiosqlite for async SQLite operations
- python-dotenv for environment management

## User Preferences
None specified yet.
