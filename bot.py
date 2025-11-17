import os
import logging
import asyncio
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
import aiosqlite
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'smxfilesbot')
TOKEN_TTL_DAYS = int(os.getenv('TOKEN_TTL_DAYS', '7'))
DB_PATH = 'file_links.db'


async def init_db():
    """Initialize the SQLite database with the required schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS file_links (
                token TEXT PRIMARY KEY,
                from_chat_id INTEGER NOT NULL,
                from_message_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                max_uses INTEGER DEFAULT 0,
                uses INTEGER DEFAULT 0
            )
        ''')
        await db.commit()
    logger.info("Database initialized successfully")


async def generate_token() -> str:
    """Generate a unique random token."""
    return secrets.token_urlsafe(16)


async def save_link(from_chat_id: int, from_message_id: int) -> str:
    """Save a forwarded message link to the database and return the token."""
    token = await generate_token()
    created_at = datetime.utcnow().isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            '''INSERT INTO file_links 
               (token, from_chat_id, from_message_id, created_at, max_uses, uses)
               VALUES (?, ?, ?, ?, 0, 0)''',
            (token, from_chat_id, from_message_id, created_at)
        )
        await db.commit()
    
    logger.info("Link saved successfully")
    return token


async def get_link(token: str) -> Optional[Tuple[int, int]]:
    """Retrieve the chat_id and message_id for a given token."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT from_chat_id, from_message_id, created_at, max_uses, uses FROM file_links WHERE token = ?',
            (token,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            from_chat_id, from_message_id, created_at, max_uses, uses = row
            
            if max_uses > 0 and uses >= max_uses:
                logger.info("Token has reached maximum uses")
                return None
            
            await db.execute(
                'UPDATE file_links SET uses = uses + 1 WHERE token = ?',
                (token,)
            )
            await db.commit()
            
            return (from_chat_id, from_message_id)


async def cleanup_old_tokens():
    """Delete tokens older than TOKEN_TTL_DAYS."""
    cutoff_date = (datetime.utcnow() - timedelta(days=TOKEN_TTL_DAYS)).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'DELETE FROM file_links WHERE created_at < ?',
            (cutoff_date,)
        )
        deleted_count = cursor.rowcount
        await db.commit()
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired tokens")


async def periodic_cleanup(context: ContextTypes.DEFAULT_TYPE):
    """Background task that runs every hour to clean up old tokens."""
    await cleanup_old_tokens()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command with optional token parameter."""
    if not update.message:
        return
    
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "👋 Welcome to the File Link Bot!\n\n"
            "📝 How to use:\n"
            "1. Forward a file or media from a Telegram channel to me\n"
            "2. I'll generate a shareable link for you\n"
            "3. Anyone with the link can access the file without seeing the original channel\n\n"
            "🔗 Links never expire!"
        )
        return
    
    token = args[0]
    logger.info("Received /start with token")
    
    link_data = await get_link(token)
    
    if not link_data:
        await update.message.reply_text(
            "❌ This link is invalid.\n\n"
            "The link may not exist or the original message was deleted."
        )
        return
    
    from_chat_id, from_message_id = link_data
    
    try:
        await context.bot.copy_message(
            chat_id=update.message.chat_id,
            from_chat_id=from_chat_id,
            message_id=from_message_id
        )
        logger.info(f"Successfully copied message from chat {from_chat_id}, message {from_message_id}")
    except Exception as e:
        logger.error(f"Failed to copy message: {e}")
        await update.message.reply_text(
            "❌ Sorry, I couldn't retrieve the file. This might happen if:\n"
            "• The original message was deleted\n"
            "• The channel is private and I don't have access\n"
            "• I was removed from the channel\n\n"
            "Please contact the person who shared this link."
        )


async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forwarded messages and generate deep-links."""
    if not update.message:
        return
    
    message = update.message
    
    if not message.forward_from_chat:
        await message.reply_text(
            "⚠️ Please forward a file from a channel.\n\n"
            "This bot only works with messages forwarded from Telegram channels."
        )
        return
    
    if message.forward_from_chat.type != 'channel':
        await message.reply_text(
            "⚠️ Please forward a file from a channel.\n\n"
            "The forwarded message must be from a Telegram channel, not from a user or group."
        )
        return
    
    from_chat_id = message.forward_from_chat.id
    from_message_id = message.forward_from_message_id
    
    if not from_message_id:
        await message.reply_text(
            "❌ Could not process this forwarded message.\n\n"
            "Please try forwarding the message again."
        )
        return
    
    token = await save_link(from_chat_id, from_message_id)
    
    deep_link = f"https://t.me/{BOT_USERNAME}?start={token}"
    
    await message.reply_text(
        f"✅ Link created successfully!\n\n"
        f"🔗 Share this link:\n{deep_link}\n\n"
        f"♾️ Never expires\n"
        f"📊 Uses: Unlimited"
    )
    
    logger.info(f"Generated deep-link for chat {from_chat_id}, message {from_message_id}")


async def post_init(application: Application):
    """Initialize the database when the bot starts."""
    await init_db()


def main():
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        print("\n❌ ERROR: BOT_TOKEN is not set!")
        print("Please set your Telegram Bot Token in Replit Secrets:")
        print("1. Click on 'Secrets' in the left sidebar")
        print("2. Add a new secret with key: BOT_TOKEN")
        print("3. Paste your bot token from @BotFather as the value")
        print("4. Restart the bot\n")
        return
    
    logger.info(f"Starting bot with username: {BOT_USERNAME}")
    logger.info(f"Token TTL: {TOKEN_TTL_DAYS} days")
    
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(
        filters.FORWARDED & ~filters.COMMAND,
        handle_forwarded_message
    ))
    
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
