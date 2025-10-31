"""
Configuration module for the Telegram bot.
Loads and validates environment variables.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # Telegram Bot Token (required)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Database connection URL (required)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Environment: development or production
    ENV: str = os.getenv("ENV", "development")

    # Webhook configuration (production only)
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    WEBHOOK_DOMAIN: str = os.getenv("WEBHOOK_DOMAIN", "")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")

    # Conversation timeout (in seconds)
    CONVERSATION_TIMEOUT: int = int(os.getenv("CONVERSATION_TIMEOUT", "600"))  # 10 minutes

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")

        if cls.ENV not in ("development", "production"):
            raise ValueError("ENV must be 'development' or 'production'")

        if cls.ENV == "production":
            if not cls.WEBHOOK_SECRET:
                raise ValueError("WEBHOOK_SECRET is required in production")
            if not cls.WEBHOOK_DOMAIN:
                raise ValueError("WEBHOOK_DOMAIN is required in production")

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return cls.ENV == "production"

    @classmethod
    def get_webhook_url(cls) -> Optional[str]:
        """Get the full webhook URL for production."""
        if not cls.is_production():
            return None
        return f"https://{cls.WEBHOOK_DOMAIN}{cls.WEBHOOK_PATH}"


# Validate configuration on import
Config.validate()
