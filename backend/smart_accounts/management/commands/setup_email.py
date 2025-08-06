"""
Django management command to configure email settings.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Configure email settings for Smart Accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backend',
            choices=['ses', 'console', 'bypass'],
            help='Email backend to use (ses/console/bypass)'
        )
        parser.add_argument(
            '--aws-key',
            help='AWS SES Access Key ID'
        )
        parser.add_argument(
            '--aws-secret',
            help='AWS SES Secret Access Key'
        )
        parser.add_argument(
            '--aws-region',
            default='us-east-1',
            help='AWS SES Region (default: us-east-1)'
        )
        parser.add_argument(
            '--from-email',
            default='noreply@smartaccounts.com',
            help='Default from email address'
        )
        parser.add_argument(
            '--bypass',
            action='store_true',
            help='Enable email verification bypass'
        )
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Show current email configuration'
        )

    def handle(self, *args, **options):
        if options['show_config']:
            self.show_current_config()
            return

        if options['backend'] == 'ses':
            self.setup_ses(options)
        elif options['backend'] == 'console':
            self.setup_console()
        elif options['backend'] == 'bypass':
            self.setup_bypass()
        elif options['bypass']:
            self.setup_bypass()
        else:
            self.stdout.write(
                self.style.WARNING('Please specify a backend or action. Use --help for options.')
            )

    def show_current_config(self):
        self.stdout.write(self.style.SUCCESS('📧 CURRENT EMAIL CONFIGURATION:'))
        self.stdout.write('-' * 40)
        
        backend = getattr(settings, 'EMAIL_BACKEND', 'Not set')
        self.stdout.write(f'EMAIL_BACKEND: {backend}')
        
        aws_key = 'Set' if getattr(settings, 'AWS_SES_ACCESS_KEY_ID') else 'Not set'
        self.stdout.write(f'AWS_SES_ACCESS_KEY_ID: {aws_key}')
        
        aws_secret = 'Set' if getattr(settings, 'AWS_SES_SECRET_ACCESS_KEY') else 'Not set'
        self.stdout.write(f'AWS_SES_SECRET_ACCESS_KEY: {aws_secret}')
        
        aws_region = getattr(settings, 'AWS_SES_REGION', 'us-east-1 (default)')
        self.stdout.write(f'AWS_SES_REGION: {aws_region}')
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartaccounts.com (default)')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {from_email}')
        
        bypass = getattr(settings, 'BYPASS_EMAIL_VERIFICATION', False)
        self.stdout.write(f'BYPASS_EMAIL_VERIFICATION: {bypass}')

    def setup_ses(self, options):
        if not options['aws_key'] or not options['aws_secret']:
            self.stdout.write(
                self.style.ERROR('AWS credentials required for SES setup. Use --aws-key and --aws-secret.')
            )
            return

        # Note: These settings would need to be persisted to environment
        # For this demo, we'll show what would be set
        self.stdout.write(self.style.SUCCESS('🔧 AWS SES Setup (Environment Variables):'))
        self.stdout.write(f'export AWS_SES_ACCESS_KEY_ID="{options["aws_key"]}"')
        self.stdout.write(f'export AWS_SES_SECRET_ACCESS_KEY="{options["aws_secret"]}"')
        self.stdout.write(f'export AWS_SES_REGION="{options["aws_region"]}"')
        self.stdout.write(f'export DEFAULT_FROM_EMAIL="{options["from_email"]}"')
        self.stdout.write('export EMAIL_BACKEND="infrastructure.email.aws_ses_backend.DevelopmentAWSSESBackend"')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('⚠️  SES SANDBOX MODE:'))
        self.stdout.write('- You can only send TO verified email addresses')
        self.stdout.write('- Verify recipient emails in AWS SES Console')
        self.stdout.write('- Or use --bypass for development')

    def setup_console(self):
        self.stdout.write(self.style.SUCCESS('🖥️  Console Email Setup (Environment Variables):'))
        self.stdout.write('export EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"')
        self.stdout.write('export BYPASS_EMAIL_VERIFICATION="False"')
        self.stdout.write('')
        self.stdout.write('✅ Emails will be displayed in Django console/logs.')

    def setup_bypass(self):
        self.stdout.write(self.style.SUCCESS('🚀 Email Bypass Setup (Environment Variables):'))
        self.stdout.write('export BYPASS_EMAIL_VERIFICATION="True"')
        self.stdout.write('export EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"')
        self.stdout.write('')
        self.stdout.write('✅ Email verification will be bypassed.')
        self.stdout.write('ℹ️  Users will be auto-verified without email confirmation.')