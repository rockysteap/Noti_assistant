"""
Main Telegram bot implementation for the Noti project with Django integration.
This is the full-featured bot with database integration, analytics, and advanced features.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from telegram.ext import Application

from django.conf import settings
from django.contrib.auth.models import User
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.error import TelegramError

from .models import (
    TelegramUser, BotConversation, BotCommand as BotCommandModel,
    BotMessage, BotAnalytics
)
from apps.notifications.models import Notification
from apps.core.exceptions import TelegramBotError

logger = logging.getLogger(__name__)

# Conversation states
(MAIN_MENU, NOTIFICATION_MENU, SETTINGS_MENU, 
 WAITING_FOR_MESSAGE, WAITING_FOR_TITLE) = range(5)


class NotiBot:
    """
    Main Telegram bot class for the Noti project with full Django integration.
    """
    
    def __init__(self):
        self.application: Optional['Application'] = None
        self.bot: Optional[Bot] = None
        self.setup_bot()
    
    def setup_bot(self):
        """Setup the Telegram bot application."""
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set, bot will not start")
            return None
        
        try:
            self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
            assert self.application is not None  # Help linter understand this is not None
            self.bot = self.application.bot
            self._setup_handlers()
            logger.info("Telegram bot setup completed successfully")
        except Exception as e:
            logger.error(f"Failed to setup Telegram bot: {e}")
            raise TelegramBotError(f"Failed to setup bot: {e}")
    
    def _setup_handlers(self):
        """Setup all bot handlers."""
        if self.application is None:
            raise TelegramBotError("Application not initialized")
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("notifications", self.notifications_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Conversation handler for interactive flows
        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler("send_notification", self.send_notification_command),
                CallbackQueryHandler(self.handle_callback, pattern="^send_notification$")
            ],
            states={
                WAITING_FOR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_title_input)],
                WAITING_FOR_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message_input)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        self.application.add_handler(conversation_handler)
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for regular messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        try:
            user = await self._get_or_create_telegram_user(update)
            
            welcome_text = f"""
🎉 Welcome to Noti Bot, {user.first_name or 'there'}!

I'm here to help you manage your notifications. You can:
• 📬 View your notifications
• ⚙️ Manage your settings
• 📊 Check your stats
• 📝 Send notifications

Use /help to see all available commands.
            """
            
            keyboard = [
                [InlineKeyboardButton("📬 My Notifications", callback_data="notifications")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
                [InlineKeyboardButton("📊 Stats", callback_data="stats")],
                [InlineKeyboardButton("📝 Send Notification", callback_data="send_notification")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            await self._log_message(update, "start_command")
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text("Sorry, something went wrong. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
🤖 **Noti Bot Commands**

**Basic Commands:**
/start - Start the bot and see main menu
/help - Show this help message
/cancel - Cancel current operation

**Notification Commands:**
/notifications - View your notifications
/send_notification - Send a new notification

**Settings & Stats:**
/settings - Manage your notification settings
/stats - View your usage statistics

**Quick Actions:**
Use the inline buttons for quick access to features!

Need help? Contact support or use /start to return to the main menu.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
        await self._log_message(update, "help_command")
    
    async def notifications_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /notifications command."""
        try:
            user = await self._get_or_create_telegram_user(update)
            django_user = user.user
            
            # Get recent notifications
            notifications = Notification.objects.filter(user=django_user).order_by('-created_at')[:10]
            
            if not notifications:
                await update.message.reply_text("📭 You have no notifications yet.")
                return
            
            text = "📬 **Your Recent Notifications:**\n\n"
            for i, notification in enumerate(notifications, 1):
                status = "✅" if notification.is_read else "🔴"
                text += f"{i}. {status} **{notification.title}**\n"
                text += f"   📅 {notification.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                text += f"   🏷️ {notification.notification_type.title()}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_notifications")],
                [InlineKeyboardButton("📝 Send New", callback_data="send_notification")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            await self._log_message(update, "notifications_command")
            
        except Exception as e:
            logger.error(f"Error in notifications_command: {e}")
            await update.message.reply_text("Sorry, couldn't fetch your notifications. Please try again.")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        try:
            user = await self._get_or_create_telegram_user(update)
            
            text = f"""
⚙️ **Your Settings**

👤 **Profile:**
• Name: {user.first_name} {user.last_name or ''}
• Username: @{user.username or 'Not set'}
• Language: {user.language_code.upper()}
• Premium: {'Yes' if user.is_premium else 'No'}

🔔 **Notification Preferences:**
• Email notifications: {'Enabled' if user.user.email else 'Disabled'}
• Telegram notifications: Enabled
• Language: {user.language_code.upper()}

Use the buttons below to manage your settings.
            """
            
            keyboard = [
                [InlineKeyboardButton("🌍 Change Language", callback_data="change_language")],
                [InlineKeyboardButton("📧 Email Settings", callback_data="email_settings")],
                [InlineKeyboardButton("🔔 Notification Types", callback_data="notification_types")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            await self._log_message(update, "settings_command")
            
        except Exception as e:
            logger.error(f"Error in settings_command: {e}")
            await update.message.reply_text("Sorry, couldn't load your settings. Please try again.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        try:
            user = await self._get_or_create_telegram_user(update)
            
            # Get user stats
            total_messages = BotMessage.objects.filter(user=user).count()
            bot_messages = BotMessage.objects.filter(user=user, is_bot_message=True).count()
            user_messages = total_messages - bot_messages
            
            # Get notification stats
            total_notifications = Notification.objects.filter(user=user.user).count()
            unread_notifications = Notification.objects.filter(user=user.user, is_read=False).count()
            
            text = f"""
📊 **Your Statistics**

💬 **Messages:**
• Total messages: {total_messages}
• Your messages: {user_messages}
• Bot responses: {bot_messages}

📬 **Notifications:**
• Total notifications: {total_notifications}
• Unread notifications: {unread_notifications}
• Read notifications: {total_notifications - unread_notifications}

📅 **Account:**
• Member since: {user.created_at.strftime('%Y-%m-%d')}
• Last activity: {user.updated_at.strftime('%Y-%m-%d %H:%M')}
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh Stats", callback_data="refresh_stats")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            await self._log_message(update, "stats_command")
            
        except Exception as e:
            logger.error(f"Error in stats_command: {e}")
            await update.message.reply_text("Sorry, couldn't load your statistics. Please try again.")
    
    async def send_notification_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /send_notification command."""
        await update.message.reply_text(
            "📝 **Send a Notification**\n\n"
            "Please enter the title for your notification:",
            parse_mode='Markdown'
        )
        return WAITING_FOR_TITLE
    
    async def handle_title_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle title input for notification."""
        context.user_data['notification_title'] = update.message.text
        await update.message.reply_text(
            "Now please enter the message content:",
            parse_mode='Markdown'
        )
        return WAITING_FOR_MESSAGE
    
    async def handle_message_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle message input for notification."""
        try:
            user = await self._get_or_create_telegram_user(update)
            title = context.user_data.get('notification_title', 'Untitled')
            message = update.message.text
            
            # Create notification
            notification = Notification.objects.create(
                user=user.user,
                title=title,
                message=message,
                notification_type='info',
                priority='normal'
            )
            
            await update.message.reply_text(
                f"✅ **Notification Created!**\n\n"
                f"**Title:** {title}\n"
                f"**Message:** {message}\n"
                f"**ID:** {notification.id}",
                parse_mode='Markdown'
            )
            
            # Clear user data
            context.user_data.clear()
            await self._log_message(update, "notification_created")
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            await update.message.reply_text("Sorry, couldn't create the notification. Please try again.")
            return ConversationHandler.END
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command."""
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "notifications":
            await self.notifications_command(update, context)
        elif data == "settings":
            await self.settings_command(update, context)
        elif data == "stats":
            await self.stats_command(update, context)
        elif data == "send_notification":
            await self.send_notification_command(update, context)
        elif data == "main_menu":
            await self.start_command(update, context)
        elif data == "refresh_notifications":
            await self.notifications_command(update, context)
        elif data == "refresh_stats":
            await self.stats_command(update, context)
        else:
            await query.edit_message_text("Unknown action. Please use /start to return to the main menu.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        try:
            user = await self._get_or_create_telegram_user(update)
            message_text = update.message.text
            
            # Simple AI-like responses based on keywords
            if any(word in message_text.lower() for word in ['hello', 'hi', 'hey']):
                await update.message.reply_text(f"Hello {user.first_name or 'there'}! 👋")
            elif any(word in message_text.lower() for word in ['thanks', 'thank you']):
                await update.message.reply_text("You're welcome! 😊")
            elif any(word in message_text.lower() for word in ['help', 'support']):
                await self.help_command(update, context)
            else:
                await update.message.reply_text(
                    "I'm not sure how to respond to that. Use /help to see available commands or /start for the main menu."
                )
            
            await self._log_message(update, "regular_message")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text("Sorry, I couldn't process your message. Please try again.")
    
    async def _get_or_create_telegram_user(self, update: Update) -> TelegramUser:
        """Get or create TelegramUser from update."""
        telegram_user = update.effective_user
        
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_user.id)
            # Update user info
            user.username = telegram_user.username or ''
            user.first_name = telegram_user.first_name or ''
            user.last_name = telegram_user.last_name or ''
            user.language_code = telegram_user.language_code or 'en'
            user.is_premium = getattr(telegram_user, 'is_premium', False)
            user.save()
            return user
        except TelegramUser.DoesNotExist:
            # Create Django user
            django_user = User.objects.create_user(
                username=f"telegram_{telegram_user.id}",
                first_name=telegram_user.first_name or '',
                last_name=telegram_user.last_name or '',
                email=f"telegram_{telegram_user.id}@noti.local"
            )
            
            # Create TelegramUser
            user = TelegramUser.objects.create(
                user=django_user,
                telegram_id=telegram_user.id,
                username=telegram_user.username or '',
                first_name=telegram_user.first_name or '',
                last_name=telegram_user.last_name or '',
                language_code=telegram_user.language_code or 'en',
                is_premium=getattr(telegram_user, 'is_premium', False)
            )
            return user
    
    async def _log_message(self, update: Update, message_type: str):
        """Log message to database."""
        try:
            user = await self._get_or_create_telegram_user(update)
            
            BotMessage.objects.create(
                user=user,
                message_id=update.message.message_id,
                message_type='text',
                content=update.message.text or '',
                is_bot_message=False
            )
            
            # Update analytics
            self._update_analytics()
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")
    
    def _update_analytics(self):
        """Update daily analytics."""
        try:
            today = datetime.now().date()
            analytics, created = BotAnalytics.objects.get_or_create(date=today)
            
            if created:
                analytics.total_users = TelegramUser.objects.count()
                analytics.active_users = 1
                analytics.messages_received = 1
            else:
                analytics.messages_received += 1
            
            analytics.save()
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong. Please try again or use /start to return to the main menu."
            )
    
    async def start_polling(self):
        """Start the bot in polling mode."""
        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Bot started in polling mode")
    
    async def stop(self):
        """Stop the bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Bot stopped")


# Global bot instance
bot_instance = None


def get_bot() -> Optional[NotiBot]:
    """Get the global bot instance."""
    global bot_instance
    if bot_instance is None:
        bot_instance = NotiBot()
    return bot_instance


def handle_telegram_update(update_data: Dict[str, Any]):
    """Handle incoming Telegram update from webhook."""
    try:
        bot = get_bot()
        if bot and bot.application:
            # Process update synchronously
            asyncio.create_task(bot.application.process_update(update_data))
            logger.info(f"Processed Telegram update: {update_data.get('update_id')}")
        else:
            logger.warning("Bot not initialized, cannot process update")
    except Exception as e:
        logger.error(f"Error processing Telegram update: {e}")


# Legacy functions for backward compatibility
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy start command."""
    bot = get_bot()
    if bot:
        await bot.start_command(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy help command."""
    bot = get_bot()
    if bot:
        await bot.help_command(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy message handler."""
    bot = get_bot()
    if bot:
        await bot.handle_message(update, context)


def setup_bot():
    """Legacy bot setup function."""
    return get_bot()
