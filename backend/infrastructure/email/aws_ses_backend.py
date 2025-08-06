"""
AWS SES Email Backend for Smart Accounts Management System.
"""
import boto3
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class AWSSESBackend(BaseEmailBackend):
    """
    Custom email backend using AWS SES.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.connection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS SES client."""
        try:
            self.connection = boto3.client(
                'ses',
                aws_access_key_id=getattr(settings, 'AWS_SES_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SES_SECRET_ACCESS_KEY', None),
                region_name=getattr(settings, 'AWS_SES_REGION', 'us-east-1')
            )
            logger.info("AWS SES client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS SES client: {e}")
            if not self.fail_silently:
                raise
    
    def open(self):
        """Open connection - SES doesn't need persistent connections."""
        return True
    
    def close(self):
        """Close connection - SES doesn't need persistent connections."""
        pass
    
    def send_messages(self, email_messages):
        """Send email messages via AWS SES."""
        if not email_messages:
            return 0
            
        sent_count = 0
        for message in email_messages:
            if self._send_message(message):
                sent_count += 1
        
        return sent_count
    
    def _send_message(self, message):
        """Send a single email message."""
        try:
            # Prepare email data
            destination = {
                'ToAddresses': message.to,
                'CcAddresses': message.cc,
                'BccAddresses': message.bcc,
            }
            
            # Handle multipart messages (HTML + Text)
            if isinstance(message, EmailMultiAlternatives) and message.alternatives:
                # Find HTML content
                html_content = None
                for content, mimetype in message.alternatives:
                    if mimetype == 'text/html':
                        html_content = content
                        break
                
                email_data = {
                    'Source': message.from_email,
                    'Destination': destination,
                    'Message': {
                        'Subject': {
                            'Data': message.subject,
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': message.body,
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                }
                
                if html_content:
                    email_data['Message']['Body']['Html'] = {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
            else:
                # Plain text message
                email_data = {
                    'Source': message.from_email,
                    'Destination': destination,
                    'Message': {
                        'Subject': {
                            'Data': message.subject,
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': message.body,
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                }
            
            # Send via SES
            response = self.connection.send_email(**email_data)
            message_id = response['MessageId']
            
            logger.info(f"Email sent successfully via SES. MessageId: {message_id}")
            logger.info(f"Subject: {message.subject}")
            logger.info(f"To: {', '.join(message.to)}")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # Handle specific SES errors
            if error_code == 'MessageRejected':
                logger.error(f"SES Message Rejected: {error_message}")
                if 'Email address not verified' in error_message:
                    logger.error("Email address not verified in SES. Please verify the sender email in AWS SES console.")
            elif error_code == 'SendingPausedException':
                logger.error("SES sending is paused for your account")
            elif error_code == 'MailFromDomainNotVerifiedException':
                logger.error("Mail-from domain not verified in SES")
            else:
                logger.error(f"SES ClientError: {error_code} - {error_message}")
            
            if not self.fail_silently:
                raise
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending email via SES: {e}")
            if not self.fail_silently:
                raise
            return False


class DevelopmentAWSSESBackend(AWSSESBackend):
    """
    Development version of AWS SES backend with additional logging and fallback.
    """
    
    def _send_message(self, message):
        """Send message with development-specific logging."""
        logger.info("=" * 50)
        logger.info("DEVELOPMENT EMAIL VIA AWS SES")
        logger.info("=" * 50)
        logger.info(f"From: {message.from_email}")
        logger.info(f"To: {', '.join(message.to)}")
        logger.info(f"Subject: {message.subject}")
        logger.info("-" * 50)
        logger.info("Body:")
        logger.info(message.body)
        logger.info("=" * 50)
        
        # Try to send via SES
        result = super()._send_message(message)
        
        if result:
            logger.info("✅ Email sent successfully via AWS SES")
        else:
            logger.warning("❌ Email failed to send via AWS SES")
            
        return result