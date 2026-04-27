from __future__ import annotations

from pathlib import Path

import yaml

from yt_transcripts.clients.youtube_data import YouTubeDataClient


class ChannelConfigBuilderService:
    """Builds channels.yaml-style configuration from channel name inputs."""

    def __init__(self, youtube_data_client: YouTubeDataClient | None = None) -> None:
        self.youtube_data_client = youtube_data_client or YouTubeDataClient()

    def build_config(self, channel_names: list[str]) -> tuple[dict, list[str]]:
        channels: list[dict] = []
        unresolved: list[str] = []

        for raw_name in channel_names:
            name = raw_name.strip()
            if not name:
                continue

            payload = self.youtube_data_client.find_channel_by_name(name)
            if payload is None:
                unresolved.append(name)
                continue

            channels.append(
                {
                    "name": payload["name"],
                    "channel_id": payload["channel_id"],
                    "enabled": True,
                    "tags": [],
                }
            )

        deduped: dict[str, dict] = {}
        for channel in channels:
            deduped[channel["channel_id"]] = channel

        return {"version": 1, "channels": list(deduped.values())}, unresolved

    def write_config(self, config_payload: dict, output_path: str) -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(config_payload, handle, sort_keys=False, allow_unicode=True)
