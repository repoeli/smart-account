import logging
from dataclasses import dataclass
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class StripeConfig:
    secret_key: str
    price_basic: str
    price_premium: str
    price_platinum: str
    webhook_secret: str
    publishable_key: str


class StripePaymentService:
    def __init__(self, config: Optional[StripeConfig] = None):
        self.config = config or StripeConfig(
            secret_key=getattr(settings, 'STRIPE_SECRET_KEY', ''),
            price_basic=getattr(settings, 'STRIPE_PRICE_BASIC', ''),
            price_premium=getattr(settings, 'STRIPE_PRICE_PREMIUM', ''),
            price_platinum=getattr(settings, 'STRIPE_PRICE_PLATINUM', ''),
            webhook_secret=getattr(settings, 'STRIPE_WEBHOOK_SECRET', ''),
            publishable_key=getattr(settings, 'STRIPE_PUBLISHABLE_KEY', ''),
        )
        self.enabled = bool(self.config.secret_key)
        try:
            import stripe  # noqa: F401
        except Exception:
            self.enabled = False

    def _ensure_customer(self, email: Optional[str]) -> Optional[str]:
        """Find or create a Stripe customer by email. Returns customer_id or None."""
        if not self.enabled or not email:
            return None
        try:
            import stripe
            stripe.api_key = self.config.secret_key
            # Try to find an existing customer by email (best-effort)
            res = stripe.Customer.list(email=email, limit=1)
            if getattr(res, 'data', None):
                return res.data[0].id
            cust = stripe.Customer.create(email=email)
            return cust.id
        except Exception:
            return None

    def create_checkout_session(self, user_id: str, price_id: Optional[str] = None, customer_id: Optional[str] = None, customer_email: Optional[str] = None) -> dict:
        if not self.enabled:
            logger.info('Stripe disabled; returning no-op checkout session')
            return { 'success': True, 'url': None }
        try:
            import stripe
            stripe.api_key = self.config.secret_key
            # Resolve price id: explicit > env basic > first active recurring price
            pid = price_id or self.config.price_basic
            if not pid:
                try:
                    prices = stripe.Price.list(active=True, limit=10, expand=['data.product'])
                    for p in prices.data:
                        if getattr(p, 'type', '') == 'recurring':
                            pid = p.id
                            break
                except Exception:
                    pid = None
            if not pid:
                return { 'success': False, 'message': 'No Stripe price configured/found' }
            cust_id = customer_id or self._ensure_customer(customer_email)
            session = stripe.checkout.Session.create(
                mode='subscription',
                line_items=[{ 'price': pid, 'quantity': 1 }],
                success_url=settings.PUBLIC_BASE_URL + '/subscription/success',
                cancel_url=settings.PUBLIC_BASE_URL + '/subscription/cancel',
                customer=cust_id if cust_id else None,
                subscription_data={
                    'metadata': { 'user_id': user_id }
                },
                metadata={ 'user_id': user_id },
            )
            return { 'success': True, 'url': session.url, 'customer_id': cust_id }
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
            etype = event['type']
            data_obj = event['data']['object'] if event.get('data') else None
            user_id = None
            price_id = None
            plan = None
            try:
                # Try to derive user_id and plan information for subscription events
                if etype.startswith('customer.subscription.') and data_obj:
                    metadata = getattr(data_obj, 'metadata', None) or data_obj.get('metadata') if isinstance(data_obj, dict) else None
                    user_id = (metadata or {}).get('user_id')
                    # Expand price info if not present
                    sub_id = getattr(data_obj, 'id', None) or data_obj.get('id')
                    if sub_id:
                        sub = stripe.Subscription.retrieve(sub_id, expand=['items.data.price.product'])
                        item = sub.items.data[0] if getattr(sub.items, 'data', None) else None
                        price = getattr(item, 'price', None)
                        price_id = getattr(price, 'id', None)
                        plan = {
                            'id': price_id,
                            'nickname': getattr(price, 'nickname', None) or getattr(getattr(price, 'product', None), 'name', None),
                            'currency': getattr(price, 'currency', None),
                            'unit_amount': getattr(price, 'unit_amount', None),
                            'interval': getattr(getattr(price, 'recurring', None), 'interval', None),
                        }
                elif etype == 'checkout.session.completed' and data_obj:
                    # Checkout session contains metadata.user_id and subscription id
                    metadata = getattr(data_obj, 'metadata', None) or data_obj.get('metadata') if isinstance(data_obj, dict) else None
                    user_id = (metadata or {}).get('user_id')
                    sub_id = getattr(data_obj, 'subscription', None) or data_obj.get('subscription')
                    if sub_id:
                        sub = stripe.Subscription.retrieve(sub_id, expand=['items.data.price.product'])
                        item = sub.items.data[0] if getattr(sub.items, 'data', None) else None
                        price = getattr(item, 'price', None)
                        price_id = getattr(price, 'id', None)
                        plan = {
                            'id': price_id,
                            'nickname': getattr(price, 'nickname', None) or getattr(getattr(price, 'product', None), 'name', None),
                            'currency': getattr(price, 'currency', None),
                            'unit_amount': getattr(price, 'unit_amount', None),
                            'interval': getattr(getattr(price, 'recurring', None), 'interval', None),
                        }
            except Exception:
                # Best-effort enrichment only
                pass
            return { 'success': True, 'event_type': etype, 'user_id': user_id, 'price_id': price_id, 'plan': plan }
        except Exception as e:
            return { 'success': False, 'message': str(e) }

    def create_billing_portal(self, customer_id: Optional[str] = None, user_id: Optional[str] = None, customer_email: Optional[str] = None) -> dict:
        if not self.enabled:
            logger.info('Stripe disabled; returning no-op portal session')
            return { 'success': True, 'url': None }
        try:
            import stripe
            stripe.api_key = self.config.secret_key
            # In a full implementation, we would look up the Stripe customer id by user
            if not customer_id:
                customer_id = self._ensure_customer(customer_email)
                if not customer_id:
                    return { 'success': True, 'url': None }
            portal = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=settings.PUBLIC_BASE_URL + '/account',
            )
            return { 'success': True, 'url': portal.url, 'customer_id': customer_id }
        except Exception as e:
            logger.warning('Stripe portal failed: %s', e)
            return { 'success': False, 'message': str(e) }

    def list_plans(self) -> dict:
        """Return available subscription plans from Stripe or env configuration.

        Shape: { success: bool, items: [ { id, nickname, currency, unit_amount, interval }... ], publishable_key }
        """
        if not self.enabled:
            # No Stripe SDK available; fall back to env-configured prices (ids only)
            items = []
            for key, nick in [
                (self.config.price_basic, 'Basic'),
                (self.config.price_premium, 'Premium'),
                (self.config.price_platinum, 'Platinum'),
            ]:
                if key:
                    items.append({ 'id': key, 'nickname': nick, 'currency': None, 'unit_amount': None, 'interval': None })
            return { 'success': True, 'items': items, 'publishable_key': self.config.publishable_key }
        try:
            import stripe
            stripe.api_key = self.config.secret_key
            prices = stripe.Price.list(active=True, expand=['data.product'])
            items = []
            for p in prices.data:
                if getattr(p, 'type', '') != 'recurring':
                    continue
                nickname = getattr(p, 'nickname', None) or getattr(p.product, 'name', None)
                # Prefer plans named Basic/Premium/Platinum but include all recurring
                items.append({
                    'id': p.id,
                    'nickname': nickname,
                    'currency': getattr(p, 'currency', None),
                    'unit_amount': getattr(p, 'unit_amount', None),
                    'interval': getattr(getattr(p, 'recurring', None), 'interval', None),
                })
            # If env prices exist, ensure they are present even if not returned above
            env_prices = [
                (self.config.price_basic, 'Basic'),
                (self.config.price_premium, 'Premium'),
                (self.config.price_platinum, 'Platinum'),
            ]
            known_ids = { it['id'] for it in items }
            for pid, nick in env_prices:
                if pid and pid not in known_ids:
                    try:
                        pr = stripe.Price.retrieve(pid, expand=['product'])
                        items.append({
                            'id': pr.id,
                            'nickname': getattr(pr, 'nickname', None) or getattr(pr.product, 'name', None) or nick,
                            'currency': getattr(pr, 'currency', None),
                            'unit_amount': getattr(pr, 'unit_amount', None),
                            'interval': getattr(getattr(pr, 'recurring', None), 'interval', None),
                        })
                    except Exception:
                        items.append({ 'id': pid, 'nickname': nick, 'currency': None, 'unit_amount': None, 'interval': None })
            return { 'success': True, 'items': items, 'publishable_key': self.config.publishable_key }
        except Exception as e:
            logger.warning('Stripe list_plans failed: %s', e)
            return { 'success': False, 'message': str(e), 'items': [], 'publishable_key': self.config.publishable_key }


