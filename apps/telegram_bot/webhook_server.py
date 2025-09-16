"""
Webhook server for Telegram bot in production.
"""

import asyncio
import logging
from typing import Dict, Any

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View

from .bot import get_bot, handle_telegram_update

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class TelegramWebhookView(View):
    """
    Webhook view for receiving Telegram updates.
    """
    
    def post(self, request):
        """Handle incoming webhook requests."""
        try:
            # Get the raw request body
            import json
            update_data = json.loads(request.body)
            
            # Verify webhook secret if configured
            secret_token = request.META.get('HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN')
            if settings.TELEGRAM_WEBHOOK_SECRET and secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
                logger.warning("Invalid webhook secret token")
                return JsonResponse({'error': 'Unauthorized'}, status=401)
            
            # Process the update
            handle_telegram_update(update_data)
            
            return JsonResponse({'status': 'ok'})
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)


class WebhookServer:
    """
    Webhook server for production deployment.
    """
    
    def __init__(self, host='0.0.0.0', port=8443):
        self.host = host
        self.port = port
        self.bot = get_bot()
    
    async def start(self):
        """Start the webhook server."""
        if not self.bot:
            logger.error("Bot not initialized")
            return
        
        try:
            # Set webhook URL
            webhook_url = f"{settings.TELEGRAM_WEBHOOK_URL}/webhook/telegram/"
            await self.bot.bot.set_webhook(
                url=webhook_url,
                secret_token=settings.TELEGRAM_WEBHOOK_SECRET
            )
            logger.info(f"Webhook set to: {webhook_url}")
            
            # Start the bot application
            await self.bot.application.initialize()
            await self.bot.application.start()
            
            logger.info(f"Webhook server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error starting webhook server: {e}")
            raise
    
    async def stop(self):
        """Stop the webhook server."""
        if self.bot:
            await self.bot.stop()
            logger.info("Webhook server stopped")


# Standalone webhook server for production
async def run_webhook_server(host='0.0.0.0', port=8443):
    """Run the webhook server."""
    server = WebhookServer(host, port)
    await server.start()
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server...")
        await server.stop()


if __name__ == '__main__':
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8443
    
    asyncio.run(run_webhook_server(host, port))
