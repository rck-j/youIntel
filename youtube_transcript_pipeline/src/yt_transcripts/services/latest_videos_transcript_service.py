from __future__ import annotations

from typing import Optional

from yt_transcripts.services.batch import BatchProcessor
from yt_transcripts.services.channel_service import ChannelService


class LatestVideosTranscriptService:
    """Orchestrates channel loading and transcript batch processing."""

    def __init__(
        self,
        channel_service: Optional[ChannelService] = None,
        batch_processor: Optional[BatchProcessor] = None,
    ) -> None:
        self.channel_service = channel_service or ChannelService()
        self.batch_processor = batch_processor or BatchProcessor()

    def process_configured_channels(
        self,
        *,
        max_videos_per_channel: int = 5,
        languages: Optional[list[str]] = None,
        enable_ytdlp_fallback: bool = True,
        enable_whisper_fallback: bool = False,
        whisper_model: str = "base",
        whisper_language: Optional[str] = None,
        output_dir: str = "outputs",
        enabled_only: bool = True,
    ) -> list[dict]:
        channel_ids = self.channel_service.get_channel_ids(enabled_only=enabled_only)
        if not channel_ids:
            return []

        return self.batch_processor.process_latest_videos(
            channel_ids=channel_ids,
            max_videos_per_channel=max_videos_per_channel,
            languages=languages,
            enable_ytdlp_fallback=enable_ytdlp_fallback,
            enable_whisper_fallback=enable_whisper_fallback,
            whisper_model=whisper_model,
            whisper_language=whisper_language,
            output_dir=output_dir,
        )
