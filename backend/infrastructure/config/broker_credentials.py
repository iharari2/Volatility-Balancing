# =========================
# backend/infrastructure/config/broker_credentials.py
# =========================
"""
Broker credentials configuration.

Loads broker API credentials from environment variables.
Supports both paper and live trading modes.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AlpacaCredentials:
    """Alpaca API credentials."""

    api_key: str
    secret_key: str
    paper: bool = True  # Default to paper trading for safety
    base_url: Optional[str] = None  # Override base URL if needed

    @classmethod
    def from_env(cls) -> "AlpacaCredentials":
        """
        Load Alpaca credentials from environment variables.

        Environment variables:
            ALPACA_API_KEY: API key (required)
            ALPACA_SECRET_KEY: Secret key (required)
            ALPACA_PAPER: Use paper trading (default: true)
            ALPACA_BASE_URL: Override base URL (optional)

        Raises:
            ValueError: If required credentials are missing
        """
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca credentials not configured. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
            )

        paper_env = os.getenv("ALPACA_PAPER", "true").lower()
        paper = paper_env in ("true", "1", "yes", "on")

        base_url = os.getenv("ALPACA_BASE_URL")

        return cls(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper,
            base_url=base_url,
        )

    @property
    def trading_url(self) -> str:
        """Get the trading API base URL."""
        if self.base_url:
            return self.base_url
        if self.paper:
            return "https://paper-api.alpaca.markets"
        return "https://api.alpaca.markets"

    @property
    def data_url(self) -> str:
        """Get the market data API base URL."""
        return "https://data.alpaca.markets"


def get_alpaca_credentials() -> AlpacaCredentials:
    """
    Get Alpaca credentials from environment.

    Returns:
        AlpacaCredentials instance

    Raises:
        ValueError: If credentials are not configured
    """
    return AlpacaCredentials.from_env()


def has_alpaca_credentials() -> bool:
    """Check if Alpaca credentials are configured."""
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    return bool(api_key and secret_key)
