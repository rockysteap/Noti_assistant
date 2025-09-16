"""
Management command to start the Telegram bot.
"""

import asyncio
import signal
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.telegram_bot.bot import get_bot


class Command(BaseCommand):
    help = 'Start the Telegram bot in polling mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--webhook',
            action='store_true',
            help='Start bot in webhook mode instead of polling'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8443,
            help='Port for webhook server (default: 8443)'
        )

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_BOT_TOKEN not set in environment variables')
            )
            return

        bot = get_bot()
        if not bot:
            self.stdout.write(
                self.style.ERROR('Failed to initialize bot')
            )
            return

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write(self.style.WARNING('\nShutting down bot...'))
            asyncio.create_task(bot.stop())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            if options['webhook']:
                self.stdout.write(
                    self.style.SUCCESS('Starting bot in webhook mode...')
                )
                # Webhook mode would require additional setup
                self.stdout.write(
                    self.style.WARNING('Webhook mode not fully implemented yet. Use polling mode.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Starting bot in polling mode...')
                )
                asyncio.run(bot.start_polling())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nBot stopped by user'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting bot: {e}')
            )
