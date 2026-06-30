"""MaintenOps Configuration — Environment + API Clients."""

import os
from dataclasses import dataclass, field
from typing import Optional

import stripe
from openai import OpenAI


@dataclass
class Settings:
    """Application settings loaded from environment."""
    # NVIDIA Nemotron
    nvidia_api_key: str = field(default_factory=lambda: os.environ.get("NVIDIA_API_KEY", ""))
    nemotron_base_url: str = "https://integrate.api.nvidia.com/v1"
    nemotron_model: str = "nvidia/nemotron-3-ultra"

    # Stripe
    stripe_secret_key: str = field(default_factory=lambda: os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY", ""))
    stripe_connect_client_id: str = field(default_factory=lambda: os.environ.get("STRIPE_CONNECT_CLIENT_ID", ""))
    stripe_webhook_secret: str = field(default_factory=lambda: os.environ.get("STRIPE_WEBHOOK_SECRET", ""))
    platform_commission_pct: float = 3.0  # 3% platform commission

    # Twilio
    twilio_account_sid: str = field(default_factory=lambda: os.environ.get("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.environ.get("TWILIO_AUTH_TOKEN", ""))
    twilio_phone_number: str = field(default_factory=lambda: os.environ.get("TWILIO_PHONE_NUMBER", ""))

    # Database
    database_url: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", "postgresql://localhost:5432/maintenops"))
    redis_url: str = field(default_factory=lambda: os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

    # App
    debug: bool = field(default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true")
    host: str = "0.0.0.0"
    port: int = 8080

    @property
    def is_configured(self) -> bool:
        """Check if critical API keys are set."""
        return bool(self.nvidia_api_key and self.stripe_secret_key and self.twilio_account_sid)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Lazy-load settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_nemotron_client() -> OpenAI:
    """Get an OpenAI-compatible client for Nemotron 3 Ultra."""
    s = get_settings()
    return OpenAI(
        base_url=s.nemotron_base_url,
        api_key=s.nvidia_api_key,
    )


def init_stripe():
    """Initialize Stripe SDK with the platform API key."""
    s = get_settings()
    if s.stripe_secret_key:
        stripe.api_key = s.stripe_secret_key


def get_api_status() -> dict:
    """Return connectivity status for all external APIs."""
    s = get_settings()
    return {
        "nvidia": bool(s.nvidia_api_key),
        "stripe": bool(s.stripe_secret_key),
        "twilio": bool(s.twilio_account_sid),
        "database": bool(s.database_url),
        "redis": bool(s.redis_url),
    }
