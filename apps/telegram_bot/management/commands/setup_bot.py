"""
Management command to setup Telegram bot webhook.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests


class Command(BaseCommand):
    help = 'Setup Telegram bot webhook'

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_BOT_TOKEN not set in environment variables')
            )
            return

        if not settings.TELEGRAM_WEBHOOK_URL:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_WEBHOOK_URL not set in environment variables')
            )
            return

        webhook_url = f"{settings.TELEGRAM_WEBHOOK_URL}/webhook/telegram/"
        
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
                data={'url': webhook_url}
            )
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS(f'Webhook set successfully: {webhook_url}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to set webhook: {response.text}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting webhook: {str(e)}')
            )
