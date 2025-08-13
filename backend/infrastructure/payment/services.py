import logging
from dataclasses import dataclass
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class StripeConfig:
    secret_key: str
    price_basic: str
    webhook_secret: str


class StripePaymentService:
    def __init__(self, config: Optional[StripeConfig] = None):
        self.config = config or StripeConfig(
            secret_key=getattr(settings, 'STRIPE_SECRET_KEY', ''),
            price_basic=getattr(settings, 'STRIPE_PRICE_BASIC', ''),
            webhook_secret=getattr(settings, 'STRIPE_WEBHOOK_SECRET', ''),
        )
        self.enabled = bool(self.config.secret_key)
        try:
            import stripe  # noqa: F401
        except Exception:
            self.enabled = False

    def create_checkout_session(self, user_id: str) -> dict:
        if not self.enabled:
            logger.info('Stripe disabled; returning no-op checkout session')
            return { 'success': True, 'url': None }
        try:
            import stripe
            stripe.api_key = self.config.secret_key
            session = stripe.checkout.Session.create(
                mode='subscription',
                line_items=[{ 'price': self.config.price_basic, 'quantity': 1 }],
                success_url=settings.PUBLIC_BASE_URL + '/subscription/success',
                cancel_url=settings.PUBLIC_BASE_URL + '/subscription/cancel',
                metadata={ 'user_id': user_id },
            )
            return { 'success': True, 'url': session.url }
        except Exception as e:
            logger.warning('Stripe checkout failed: %s', e)
            return { 'success': False, 'message': str(e) }

    def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        if not self.enabled:
            return { 'success': True, 'event': None }
        try:
            import stripe
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=self.config.webhook_secret,
            )
            # Minimal handling; application layer can be wired later
            return { 'success': True, 'event_type': event['type'] }
        except Exception as e:
            return { 'success': False, 'message': str(e) }

    def create_billing_portal(self, customer_id: Optional[str] = None, user_id: Optional[str] = None) -> dict:
        if not self.enabled:
            logger.info('Stripe disabled; returning no-op portal session')
            return { 'success': True, 'url': None }
        try:
            import stripe
            stripe.api_key = self.config.secret_key
            # In a full implementation, we would look up the Stripe customer id by user
            if not customer_id:
                # no customer yet; no-op
                return { 'success': True, 'url': None }
            portal = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=settings.PUBLIC_BASE_URL + '/account',
            )
            return { 'success': True, 'url': portal.url }
        except Exception as e:
            logger.warning('Stripe portal failed: %s', e)
            return { 'success': False, 'message': str(e) }


