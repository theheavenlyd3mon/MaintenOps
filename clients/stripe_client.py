"""Stripe client — payment processing, Connect, subscriptions."""

import stripe
from config import get_settings


def ensure_initialized():
    """Ensure Stripe is initialized with the platform API key."""
    s = get_settings()
    if not stripe.api_key:
        stripe.api_key = s.stripe_secret_key


async def create_owner_customer(name: str, email: str, phone: str = "") -> dict:
    """Create a Stripe customer for a property owner."""
    ensure_initialized()
    customer = stripe.Customer.create(
        name=name,
        email=email,
        phone=phone or None,
    )
    return {"id": customer.id, "email": customer.email, "name": customer.name}


async def create_subscription(customer_id: str, units: int, price_id: str = "price_per_door_15") -> dict:
    """Create monthly subscription for per-door SaaS billing."""
    ensure_initialized()
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id, "quantity": units}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
    )
    return {
        "id": subscription.id,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "latest_invoice": subscription.latest_invoice.id if subscription.latest_invoice else None,
    }


async def pay_vendor(
    vendor_connect_account_id: str,
    amount_cents: int,
    commission_pct: float = 3.0,
    transfer_group: str = "",
    description: str = "",
) -> dict:
    """Pay a vendor via Stripe Connect transfer with platform commission split.

    Args:
        vendor_connect_account_id: Stripe Connect account ID of the vendor
        amount_cents: Total payment amount in cents (e.g., 85000 for $850)
        commission_pct: Platform commission percentage (default 3.0)
        transfer_group: Group identifier for traceability
        description: Description of the payment

    Returns:
        Dict with transfer details including the commission split
    """
    ensure_initialized()
    commission_cents = int(amount_cents * commission_pct / 100)
    vendor_amount_cents = amount_cents - commission_cents

    transfer = stripe.Transfer.create(
        amount=vendor_amount_cents,
        currency="usd",
        destination=vendor_connect_account_id,
        transfer_group=transfer_group,
        metadata={"description": description},
    )

    return {
        "transfer_id": transfer.id,
        "total_amount_cents": amount_cents,
        "commission_cents": commission_cents,
        "commission_pct": commission_pct,
        "vendor_amount_cents": vendor_amount_cents,
        "transfer_group": transfer_group,
        "status": transfer.status,
    }


async def create_payment_intent(amount_cents: int, customer_id: str, capture_method: str = "automatic") -> dict:
    """Create a Stripe PaymentIntent for owner charges."""
    ensure_initialized()
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        customer=customer_id,
        capture_method=capture_method,
        automatic_payment_methods={"enabled": True},
    )
    return {
        "id": intent.id,
        "amount": intent.amount,
        "status": intent.status,
        "client_secret": intent.client_secret,
    }


async def handle_webhook_event(payload: bytes, sig_header: str) -> dict:
    """Validate and process a Stripe webhook event."""
    ensure_initialized()
    s = get_settings()
    event = stripe.Webhook.construct_event(
        payload, sig_header, s.stripe_webhook_secret
    )
    return {"type": event.type, "data": event.data.object, "id": event.id}


async def get_platform_balance() -> dict:
    """Get the current Stripe platform balance."""
    ensure_initialized()
    balance = stripe.Balance.retrieve()
    return {
        "available": [{"amount": b.amount, "currency": b.currency} for b in balance.available],
        "pending": [{"amount": b.amount, "currency": b.currency} for b in balance.pending],
    }
