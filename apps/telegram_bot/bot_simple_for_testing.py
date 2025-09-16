"""
Simple Telegram bot for testing and basic functionality.
This is the simple bot implementation for testing purposes.
"""

import asyncio
import logging
import os
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context):
    """Handle /start command."""
    welcome_text = """
🤖 **Welcome to Noti Bot!**

I'm your notification assistant. Here's what I can do:

• 📬 View your notifications
• ⚙️ Manage your settings  
• 📊 Check your stats
• 📝 Send notifications

Use /help to see all available commands.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context):
    """Handle /help command."""
    help_text = """
🤖 **Noti Bot Commands**

**Basic Commands:**
/start - Start the bot and see main menu
/help - Show this help message

**Notification Commands:**
/notifications - View your notifications
/send_notification - Send a new notification

**Settings & Stats:**
/settings - Manage your notification settings
/stats - View your usage statistics

Need help? Contact support or use /start to return to the main menu.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def notifications_command(update: Update, context):
    """Handle /notifications command."""
    await update.message.reply_text("📬 Your notifications will appear here once the full system is connected.")

async def settings_command(update: Update, context):
    """Handle /settings command."""
    await update.message.reply_text("⚙️ Settings panel will be available once the full system is connected.")

async def stats_command(update: Update, context):
    """Handle /stats command."""
    await update.message.reply_text("📊 Your statistics will appear here once the full system is connected.")

async def send_notification_command(update: Update, context):
    """Handle /send_notification command."""
    await update.message.reply_text("📝 Send notification feature will be available once the full system is connected.")

async def handle_message(update: Update, context):
    """Handle regular text messages."""
    await update.message.reply_text(f"Thanks for your message: '{update.message.text}'\n\nUse /help to see available commands.")

async def main():
    """Main function to run the bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('notifications', notifications_command))
    app.add_handler(CommandHandler('settings', settings_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('send_notification', send_notification_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting Noti Bot...")
    
    # Start the bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    logger.info("Bot is running! Press Ctrl+C to stop.")
    
    try:
        # Keep the bot running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    asyncio.run(main())

