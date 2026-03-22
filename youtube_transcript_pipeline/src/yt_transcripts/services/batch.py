from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from yt_transcripts.clients.youtube_data import YouTubeDataClient
from yt_transcripts.models.video import VideoItem
from yt_transcripts.services.pipeline import TranscriptPipeline


class BatchProcessor:
    def __init__(
        self,
        youtube_client: Optional[YouTubeDataClient] = None,
        pipeline: Optional[TranscriptPipeline] = None,
    ) -> None:
        self.youtube_client = youtube_client or YouTubeDataClient()
        self.pipeline = pipeline or TranscriptPipeline()

    def process_latest_videos(
        self,
        channel_ids: list[str],
        max_videos_per_channel: int = 5,
        languages: Optional[list[str]] = None,
        enable_ytdlp_fallback: bool = True,
        enable_whisper_fallback: bool = False,
        whisper_model: str = "base",
        whisper_language: Optional[str] = None,
        output_dir: str = "outputs",
    ) -> list[dict]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        batch_results: list[dict] = []

        for channel_id in channel_ids:
            videos = self.youtube_client.get_latest_videos(
                channel_id=channel_id,
                max_results=max_videos_per_channel,
            )

            for video in videos:
                transcript = self.pipeline.get_transcript(
                    video=video.url,
                    languages=languages or ["en"],
                    enable_ytdlp_fallback=enable_ytdlp_fallback,
                    enable_whisper_fallback=enable_whisper_fallback,
                    whisper_model=whisper_model,
                    whisper_language=whisper_language,
                )
                record = self._build_record(video, transcript.to_dict())
                batch_results.append(record)
                self._write_record(output_path=output_path, video=video, record=record)

        summary_path = output_path / "batch_summary.json"
        summary_path.write_text(json.dumps(batch_results, indent=2), encoding="utf-8")
        return batch_results

    @staticmethod
    def _build_record(video: VideoItem, transcript: dict) -> dict:
        return {
            "video": asdict(video),
            "transcript": transcript,
        }

    @staticmethod
    def _write_record(output_path: Path, video: VideoItem, record: dict) -> None:
        file_path = output_path / f"{video.video_id}.json"
        file_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
