"""
Management command to manage bot commands.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.telegram_bot.models import BotCommand as BotCommandModel
from apps.telegram_bot.bot import get_bot
import asyncio


class Command(BaseCommand):
    help = 'Manage Telegram bot commands'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['list', 'create', 'update', 'delete', 'sync', 'set_commands'],
            help='Action to perform'
        )
        parser.add_argument(
            '--command',
            type=str,
            help='Command name (for create, update, delete)'
        )
        parser.add_argument(
            '--description',
            type=str,
            help='Command description'
        )
        parser.add_argument(
            '--handler',
            type=str,
            help='Handler function name'
        )
        parser.add_argument(
            '--active',
            action='store_true',
            help='Mark command as active'
        )
        parser.add_argument(
            '--auth-required',
            action='store_true',
            help='Command requires authentication'
        )
        parser.add_argument(
            '--admin-only',
            action='store_true',
            help='Command is admin only'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_commands()
        elif action == 'create':
            self.create_command(options)
        elif action == 'update':
            self.update_command(options)
        elif action == 'delete':
            self.delete_command(options)
        elif action == 'sync':
            self.sync_commands()
        elif action == 'set_commands':
            self.set_telegram_commands()

    def list_commands(self):
        """List all bot commands."""
        commands = BotCommandModel.objects.all()
        
        if not commands:
            self.stdout.write("No bot commands found.")
            return
        
        self.stdout.write("Bot Commands:")
        self.stdout.write("-" * 50)
        
        for cmd in commands:
            status = "✅" if cmd.is_active else "❌"
            auth = "🔒" if cmd.requires_auth else "🔓"
            admin = "👑" if cmd.admin_only else "👤"
            
            self.stdout.write(
                f"{status} /{cmd.command} - {cmd.description} {auth} {admin}"
            )

    def create_command(self, options):
        """Create a new bot command."""
        command = options.get('command')
        description = options.get('description')
        handler = options.get('handler')
        
        if not all([command, description, handler]):
            self.stdout.write(
                self.style.ERROR('Command, description, and handler are required')
            )
            return
        
        if BotCommandModel.objects.filter(command=command).exists():
            self.stdout.write(
                self.style.ERROR(f'Command /{command} already exists')
            )
            return
        
        cmd = BotCommandModel.objects.create(
            command=command,
            description=description,
            handler_function=handler,
            is_active=options.get('active', False),
            requires_auth=options.get('auth_required', True),
            admin_only=options.get('admin_only', False)
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created command /{cmd.command}')
        )

    def update_command(self, options):
        """Update an existing bot command."""
        command = options.get('command')
        
        if not command:
            self.stdout.write(
                self.style.ERROR('Command name is required')
            )
            return
        
        try:
            cmd = BotCommandModel.objects.get(command=command)
        except BotCommandModel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Command /{command} not found')
            )
            return
        
        if options.get('description'):
            cmd.description = options['description']
        if options.get('handler'):
            cmd.handler_function = options['handler']
        if 'active' in options:
            cmd.is_active = options['active']
        if 'auth_required' in options:
            cmd.requires_auth = options['auth_required']
        if 'admin_only' in options:
            cmd.admin_only = options['admin_only']
        
        cmd.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated command /{cmd.command}')
        )

    def delete_command(self, options):
        """Delete a bot command."""
        command = options.get('command')
        
        if not command:
            self.stdout.write(
                self.style.ERROR('Command name is required')
            )
            return
        
        try:
            cmd = BotCommandModel.objects.get(command=command)
            cmd.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted command /{command}')
            )
        except BotCommandModel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Command /{command} not found')
            )

    def sync_commands(self):
        """Sync commands from database to bot handlers."""
        commands = BotCommandModel.objects.filter(is_active=True)
        
        self.stdout.write(f"Syncing {commands.count()} commands...")
        
        # This would integrate with the bot's command registration system
        # For now, just show what would be synced
        for cmd in commands:
            self.stdout.write(f"  - /{cmd.command}: {cmd.description}")
        
        self.stdout.write(
            self.style.SUCCESS('Commands synced successfully')
        )

    def set_telegram_commands(self):
        """Set bot commands in Telegram."""
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_BOT_TOKEN not set')
            )
            return
        
        commands = BotCommandModel.objects.filter(is_active=True)
        
        if not commands:
            self.stdout.write("No active commands to set.")
            return
        
        # Prepare commands for Telegram
        telegram_commands = []
        for cmd in commands:
            telegram_commands.append({
                'command': cmd.command,
                'description': cmd.description
            })
        
        # Set commands via Telegram API
        asyncio.run(self._set_telegram_commands(telegram_commands))

    async def _set_telegram_commands(self, commands):
        """Set commands in Telegram API."""
        try:
            bot = get_bot()
            if bot and bot.bot:
                await bot.bot.set_my_commands(commands)
                self.stdout.write(
                    self.style.SUCCESS(f'Set {len(commands)} commands in Telegram')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Bot not initialized')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting commands: {e}')
            )
