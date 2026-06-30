"""MaintenOps Configuration — Environment + API Clients."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Load .env before reading any env vars
_env_paths = [
    Path(__file__).parent / ".env",
    Path.home() / ".hermes" / "profiles" / "maintenops" / ".env",
]
for _ep in _env_paths:
    if _ep.exists():
        with open(_ep) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _key, _val = _line.split('=', 1)
                    os.environ.setdefault(_key.strip(), _val.strip())
        break

import stripe
from openai import OpenAI


@dataclass
class Settings:
    """Application settings loaded from environment."""
    # NVIDIA Nemotron
    nvidia_api_key: str = field(default_factory=lambda: os.environ.get("NVIDIA_API_KEY", ""))
    nemotron_base_url: str = "https://integrate.api.nvidia.com/v1"
    nemotron_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

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


def get_settings() -> Settings:
    """Settings — always reads fresh from environment."""
    return Settings()


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
