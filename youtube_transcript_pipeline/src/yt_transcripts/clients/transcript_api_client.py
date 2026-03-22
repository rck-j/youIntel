from __future__ import annotations

from youtube_transcript_api import YouTubeTranscriptApi

from yt_transcripts.models.transcript import TranscriptResult, TranscriptSegment


class TranscriptApiClient:
    def fetch(self, video_id: str, languages: list[str]) -> TranscriptResult:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        segments = [
            TranscriptSegment(
                text=str(item.text).replace("\n", " ").strip(),
                start=float(item.start),
                duration=float(item.duration),
            )
            for item in fetched
            if str(item.text).strip()
        ]
        transcript_text = " ".join(segment.text for segment in segments).strip()

        return TranscriptResult(
            video_id=video_id,
            source="transcript_api",
            language_code=getattr(fetched, "language_code", None),
            language=getattr(fetched, "language", None),
            is_generated=getattr(fetched, "is_generated", None),
            transcript_text=transcript_text,
            segments=segments,
            metadata={"requested_languages": languages},
        )
