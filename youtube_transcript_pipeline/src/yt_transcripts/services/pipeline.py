from __future__ import annotations

import logging
from typing import Optional

from yt_transcripts.clients.subtitle_client import YtDlpSubtitleClient
from yt_transcripts.clients.transcript_api_client import TranscriptApiClient
from yt_transcripts.clients.whisper_client import WhisperClient
from yt_transcripts.models.transcript import TranscriptResult
from yt_transcripts.services.utils import extract_video_id


LOGGER = logging.getLogger(__name__)


class TranscriptPipeline:
    def __init__(
        self,
        transcript_api_client: Optional[TranscriptApiClient] = None,
        subtitle_client: Optional[YtDlpSubtitleClient] = None,
        whisper_client: Optional[WhisperClient] = None,
    ) -> None:
        self.transcript_api_client = transcript_api_client or TranscriptApiClient()
        self.subtitle_client = subtitle_client or YtDlpSubtitleClient()
        self.whisper_client = whisper_client or WhisperClient()

    def get_transcript(
        self,
        video: str,
        languages: Optional[list[str]] = None,
        enable_ytdlp_fallback: bool = True,
        enable_whisper_fallback: bool = True,
        whisper_model: str = "base",
        whisper_language: Optional[str] = None,
    ) -> TranscriptResult:
        video_id = extract_video_id(video)
        video_url = video if video.startswith("http") else f"https://www.youtube.com/watch?v={video_id}"
        languages = languages or ["en"]

        print(f"[1/3] Trying youtube-transcript-api for {video_id}", flush=True)
        try:
            result = self.transcript_api_client.fetch(video_id=video_id, languages=languages)
            if result.transcript_text:
                return result
        except Exception as exc:  # broad on purpose: library exceptions vary by version
            LOGGER.warning("Phase 1 failed for %s: %s", video_id, exc)

        if enable_ytdlp_fallback:
            print(f"[2/3] Trying yt-dlp fallback for {video_id}", flush=True)
            try:
                result = self.subtitle_client.fetch(
                    video_url=video_url,
                    video_id=video_id,
                    languages=languages,
                )
                if result.transcript_text:
                    return result
            except Exception as exc:
                LOGGER.warning("Phase 2 failed for %s: %s", video_id, exc)

        if enable_whisper_fallback:
            print(f"[3/3] Trying Whisper fallback for {video_id}", flush=True)
            try:
                result = self.whisper_client.transcribe(
                    video_url=video_url,
                    video_id=video_id,
                    model_name=whisper_model,
                    language=whisper_language,
                )
                if result.transcript_text:
                    return result
            except Exception as exc:
                LOGGER.warning("Phase 3 failed for %s: %s", video_id, exc)

        return TranscriptResult(
            video_id=video_id,
            source="none",
            no_transcript=True,
            error="All transcript retrieval methods failed.",
            metadata={
                "attempted_languages": languages,
                "enable_ytdlp_fallback": enable_ytdlp_fallback,
                "enable_whisper_fallback": enable_whisper_fallback,
                "whisper_model": whisper_model,
            },
        )
