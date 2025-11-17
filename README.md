# Telegram File Link Bot

A Telegram bot that generates shareable deep-links for files and media forwarded from Telegram channels. Users can share these links to give others access to channel content without revealing the original source or showing "Forwarded from..." attribution.

## Features

- 🔗 Generate shareable deep-links for channel content
- 📁 Support for all file and media types
- 🔒 No "Forwarded from..." attribution when sharing
- ⏱ Automatic cleanup of expired links (7 days default)
 - ⏱ Automatic cleanup of expired links (disabled by default; links never expire)
- 💾 SQLite database for persistence
- 📊 Track link usage statistics
- ❌ Comprehensive error handling

## How It Works

1. **User forwards a file/media** from a Telegram channel to the bot
2. **Bot generates a unique token** and stores the reference to the original message
3. **Bot returns a deep-link** like: `https://t.me/smxfilesbot?start=<token>`
4. **Anyone clicks the link** and receives the original content via `/start <token>`
5. **Bot copies the message** using `copy_message()` (no forwarding attribution)

## Setup Instructions

### Prerequisites

- Python 3.11+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Environment Variables

Set these in Replit Secrets or in a `.env` file:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BOT_TOKEN` | Your Telegram Bot Token from @BotFather | ✅ Yes | - |
| `BOT_USERNAME` | Your bot's username (without @) | No | smxfilesbot |
| `TOKEN_TTL_DAYS` | Days before links expire | No | 7 |

If you prefer to store environment variables in a file while developing locally, copy the included example:

```bash
cp .env.example .env
```

Then edit `.env` and replace the placeholder values (do NOT commit your real `.env`).

When deploying to Render, set the same variables through the Render dashboard's Environment section (do not upload a `.env` file to the repo).

### Render runtime pin

Render may select a newer Python version by default. `python-telegram-bot==20.7` is not compatible with Python 3.13; to avoid runtime errors pin a supported Python version by adding a `runtime.txt` file at the repo root (example already included):

```
python-3.11.4
```

After adding `runtime.txt` re-deploy the service on Render so the correct Python runtime is used.

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your environment variables in Replit Secrets:
   - Click "Secrets" in the left sidebar
   - Add `BOT_TOKEN` with your bot token
   - Optionally add `BOT_USERNAME` and `TOKEN_TTL_DAYS`
    - Optionally add `BOT_USERNAME`. `TOKEN_TTL_DAYS` is optional — set to a positive integer to enable automatic expiry. Set to `0` (the default) to keep links indefinitely.

3. Run the bot:
```bash
python bot.py
```

## Usage

### For Users

1. **Create a link:**
   - Forward any file or media from a Telegram channel to the bot
   - Receive a shareable deep-link

2. **Access a link:**
   - Click on a deep-link or send `/start <token>` to the bot
   - Receive the original content instantly

3. **Get help:**
   - Send `/start` without parameters for instructions

### Example Flow

```
User: [Forwards a video from a channel]

Bot: ✅ Link created successfully!

     🔗 Share this link:
     https://t.me/smxfilesbot?start=abc123xyz

     ⏱ Valid for 7 days
     📊 Uses: Unlimited


User: [Shares link with friend]

Friend: [Clicks link or sends /start abc123xyz]

Bot: [Sends the video without "Forwarded from..." attribution]
```

## Database Schema

The bot uses SQLite with the following schema:

```sql
CREATE TABLE file_links (
    token TEXT PRIMARY KEY,
    from_chat_id INTEGER NOT NULL,
    from_message_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    max_uses INTEGER DEFAULT 0,
    uses INTEGER DEFAULT 0
);
```

## Features Breakdown

### Token Management
- Cryptographically secure random tokens (16 bytes, URL-safe)
- Automatic expiration after configurable TTL
- Usage tracking (currently unlimited uses)

### Cleanup Task
- Runs every hour automatically
- Deletes tokens older than `TOKEN_TTL_DAYS`
- Non-blocking async operations

### Error Handling
- Invalid or expired tokens
- Non-channel forwards
- Missing permissions
- Deleted messages
- Private channels

## Technical Details

- **Framework:** python-telegram-bot v20.7
- **Database:** SQLite with aiosqlite (async)
- **Python Version:** 3.11+
- **Architecture:** Async/await pattern throughout

## Logging

The bot includes comprehensive logging for debugging:
- Database operations
- Token generation and validation
- Message copying attempts
- Cleanup operations
- Errors and exceptions

## Troubleshooting

### Bot doesn't respond
- Verify `BOT_TOKEN` is set correctly
- Check that the bot is running without errors
- Ensure the bot isn't banned or rate-limited

### "Could not retrieve the file" error
- Original message may have been deleted
- Bot might not have access to the channel
- Channel might be private

### Links expire immediately
- Check `TOKEN_TTL_DAYS` value
- Verify system time is correct

## License

This project is open source and available for personal and commercial use.

## Support

For issues or questions, please contact the bot administrator.
