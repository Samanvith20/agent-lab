from pathlib import Path

import yaml


def load_config() -> dict:
    """Load settings from the adjacent config.yaml file."""
    return yaml.safe_load(Path(__file__).with_name("config.yaml").read_text(encoding="utf-8-sig"))


config = load_config()
