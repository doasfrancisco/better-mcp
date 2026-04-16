"""Beeper Desktop API client — thin wrapper around the official SDK."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from beeper_desktop_api import BeeperDesktop


def build_client() -> BeeperDesktop:
    """Build a BeeperDesktop client using the token from the repo root .env."""
    return BeeperDesktop(access_token=os.getenv("BEEPER_ACCESS_TOKEN"))
