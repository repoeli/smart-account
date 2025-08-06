"""
Email service infrastructure.
Handles email sending for the application.
"""

from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending various types of emails.
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.site_name = getattr(settings, 'SITE_NAME', 'Smart Accounts')
        self.site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        
        # Email bypass settings - gives you control over email verification
        self.bypass_email_verification = getattr(settings, 'BYPASS_EMAIL_VERIFICATION', False)
        self.auto_verify_development_users = getattr(settings, 'AUTO_VERIFY_DEVELOPMENT_USERS', False)
    
    def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_token: str
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            to_email: Recipient email address
            user_name: User's full name
            verification_token: Verification token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Check if email verification is bypassed
        if self.bypass_email_verification:
            logger.info(f"📧 Email verification bypassed for {to_email} (BYPASS_EMAIL_VERIFICATION=True)")
            logger.info(f"🔗 Verification URL would be: {self.site_url}/verify-email?token={verification_token}")
            return True
            
        # Log email sending attempt
        logger.info(f"📧 Sending verification email to {to_email}")
        logger.info(f"📧 Using email backend: {settings.EMAIL_BACKEND}")
        subject = f"Verify your {self.site_name} account"
        
        # Create verification URL
        verification_url = f"{self.site_url}/verify-email?token={verification_token}"
        
        # Email content
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to {self.site_name}!</h2>
            <p>Hi {user_name},</p>
            <p>Thank you for registering with {self.site_name}. To complete your registration, please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email Address</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account with {self.site_name}, please ignore this email.</p>
            <p>Best regards,<br>The {self.site_name} Team</p>
        </body>
        </html>
        """
        
        plain_text = strip_tags(html_content)
        
        try:
            send_mail(
                subject=subject,
                message=plain_text,
                from_email=self.from_email,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False
            )
            logger.info(f"✅ Verification email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send verification email to {to_email}: {e}")
            logger.error(f"📧 Email backend: {settings.EMAIL_BACKEND}")
            logger.error(f"📧 From email: {self.from_email}")
            
            # Check if this is a SES sandbox limitation
            if 'Email address not verified' in str(e):
                logger.error("🚨 SES SANDBOX MODE: The recipient email must be verified in AWS SES console!")
                logger.error(f"🔧 To fix: Go to AWS SES Console → Verified identities → Add {to_email}")
                logger.error("🔧 Or move SES out of sandbox mode to send to any email address")
                
            return False
    
    def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_token: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            to_email: Recipient email address
            user_name: User's full name
            reset_token: Password reset token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Reset your {self.site_name} password"
        
        # Create reset URL
        reset_url = f"{self.site_url}/reset-password?token={reset_token}"
        
        # Email content
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {user_name},</p>
            <p>We received a request to reset your password for your {self.site_name} account. Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
            <p>Best regards,<br>The {self.site_name} Team</p>
        </body>
        </html>
        """
        
        plain_text = strip_tags(html_content)
        
        try:
            send_mail(
                subject=subject,
                message=plain_text,
                from_email=self.from_email,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False
            )
            return True
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Failed to send password reset email to {to_email}: {e}")
            return False
    
    def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> bool:
        """
        Send welcome email after successful verification.
        
        Args:
            to_email: Recipient email address
            user_name: User's full name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Welcome to {self.site_name}!"
        
        # Email content
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to {self.site_name}!</h2>
            <p>Hi {user_name},</p>
            <p>Your email has been verified successfully! You can now log in to your {self.site_name} account and start managing your receipts and expenses.</p>
            <p><a href="{self.site_url}/login" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Log In Now</a></p>
            <p>Here's what you can do with {self.site_name}:</p>
            <ul>
                <li>Upload and digitize receipts</li>
                <li>Track expenses and income</li>
                <li>Generate reports for tax purposes</li>
                <li>Manage your business finances</li>
            </ul>
            <p>If you have any questions, feel free to contact our support team.</p>
            <p>Best regards,<br>The {self.site_name} Team</p>
        </body>
        </html>
        """
        
        plain_text = strip_tags(html_content)
        
        try:
            send_mail(
                subject=subject,
                message=plain_text,
                from_email=self.from_email,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False
            )
            return True
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Failed to send welcome email to {to_email}: {e}")
            return False
    
    def send_receipt_processed_email(
        self,
        to_email: str,
        user_name: str,
        receipt_count: int,
        total_amount: float
    ) -> bool:
        """
        Send email notification when receipts are processed.
        
        Args:
            to_email: Recipient email address
            user_name: User's full name
            receipt_count: Number of receipts processed
            total_amount: Total amount from receipts
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Receipts processed - {self.site_name}"
        
        # Email content
        html_content = f"""
        <html>
        <body>
            <h2>Receipts Processed Successfully</h2>
            <p>Hi {user_name},</p>
            <p>Great news! We've successfully processed {receipt_count} receipt(s) from your recent upload.</p>
            <p>Total amount processed: £{total_amount:.2f}</p>
            <p><a href="{self.site_url}/dashboard" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Dashboard</a></p>
            <p>You can now view and manage these receipts in your dashboard.</p>
            <p>Best regards,<br>The {self.site_name} Team</p>
        </body>
        </html>
        """
        
        plain_text = strip_tags(html_content)
        
        try:
            send_mail(
                subject=subject,
                message=plain_text,
                from_email=self.from_email,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False
            )
            return True
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Failed to send receipt processed email to {to_email}: {e}")
            return False 