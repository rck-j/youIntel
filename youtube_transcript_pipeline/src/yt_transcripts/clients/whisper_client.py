from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Optional

import yt_dlp

from yt_transcripts.models.transcript import TranscriptResult, TranscriptSegment


class WhisperClient:
    def transcribe(
        self,
        video_url: str,
        video_id: str,
        model_name: str = "base",
        language: Optional[str] = None,
    ) -> TranscriptResult:
        with tempfile.TemporaryDirectory(prefix="yt_audio_") as tmp_dir:
            audio_path = Path(tmp_dir) / f"{video_id}.mp3"
            output_template = str(Path(tmp_dir) / f"{video_id}.%(ext)s")
            ydl_opts: dict[str, Any] = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            if not audio_path.exists():
                candidates = list(Path(tmp_dir).glob(f"{video_id}.*"))
                if not candidates:
                    raise FileNotFoundError("No audio file was produced for Whisper transcription.")
                audio_path = candidates[0]

            import whisper

            model = whisper.load_model(model_name)
            kwargs: dict[str, Any] = {}
            if language:
                kwargs["language"] = language
            result = model.transcribe(str(audio_path), **kwargs)

            segments = [
                TranscriptSegment(
                    text=str(item.get("text", "")).strip(),
                    start=float(item.get("start", 0.0)),
                    duration=max(0.0, float(item.get("end", 0.0)) - float(item.get("start", 0.0))),
                )
                for item in result.get("segments", [])
                if str(item.get("text", "")).strip()
            ]

            return TranscriptResult(
                video_id=video_id,
                source="whisper",
                language_code=result.get("language"),
                language=result.get("language"),
                is_generated=True,
                transcript_text=result.get("text", "").strip(),
                segments=segments,
                metadata={
                    "phase": "whisper",
                    "title": info.get("title"),
                    "whisper_model": model_name,
                },
            )
