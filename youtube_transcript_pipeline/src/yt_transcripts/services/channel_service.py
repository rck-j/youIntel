from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml


class ChannelService:
    """Loads channel definitions from a YAML configuration file."""

    def __init__(self, config_path: str = "config/channels.yaml") -> None:
        self.config_path = Path(config_path)

    def get_channel_ids(self, *, enabled_only: bool = True) -> list[str]:
        payload = self._read_config()
        channels = payload.get("channels", [])

        channel_ids: list[str] = []
        for channel in channels:
            if not isinstance(channel, dict):
                continue
            if enabled_only and channel.get("enabled", True) is False:
                continue

            channel_id = channel.get("channel_id")
            if channel_id:
                channel_ids.append(str(channel_id))

        return channel_ids

    def _read_config(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Channel configuration file was not found: {self.config_path}"
            )

        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        if raw is None:
            return {"channels": []}
        if not isinstance(raw, dict):
            raise ValueError("Channel configuration root must be a mapping/object.")
        return raw
