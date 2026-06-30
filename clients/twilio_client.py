"""Twilio client — SMS send and receive."""

from twilio.rest import Client
from config import get_settings


_client: Client | None = None


def get_twilio_client() -> Client:
    """Get or create Twilio REST client."""
    global _client
    if _client is None:
        s = get_settings()
        _client = Client(s.twilio_account_sid, s.twilio_auth_token)
    return _client


async def send_sms(to: str, body: str) -> dict:
    """Send an SMS message to a tenant or vendor."""
    client = get_twilio_client()
    s = get_settings()
    message = client.messages.create(
        body=body,
        from_=s.twilio_phone_number,
        to=to,
    )
    return {
        "sid": message.sid,
        "status": message.status,
        "to": to,
        "body_preview": body[:50] + ("..." if len(body) > 50 else ""),
    }


async def parse_incoming_sms(form_data: dict) -> dict:
    """Parse an incoming Twilio SMS webhook payload into a structured report.

    Twilio webhook POST includes: Body, From, To, MessageSid, etc.
    """
    return {
        "from_number": form_data.get("From", ""),
        "to_number": form_data.get("To", ""),
        "body": form_data.get("Body", ""),
        "message_sid": form_data.get("MessageSid", ""),
    }
