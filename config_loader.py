"""
Configuration loader for the Reddit comment bot.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Any

import yaml


CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class Config:
    subreddits: list[str]
    topics: list[dict[str, Any]]
    settings: dict[str, Any]
    product: dict[str, Any]


def load_config(path: Path | None = None) -> Config:
    """Load and validate configuration from YAML file."""
    path = path or CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    product = data.get("product") or data.get("shopify_app", {})

    return Config(
        subreddits=data.get("subreddits", []),
        topics=data.get("topics", []),
        settings=data.get("settings", {}),
        product=product,
    )
