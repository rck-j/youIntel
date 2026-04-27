from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(slots=True)
class TranscriptSegment:
    text: str
    start: float
    duration: float


@dataclass(slots=True)
class TranscriptResult:
    video_id: str
    source: str  # transcript_api | yt_dlp | whisper | none
    language_code: Optional[str] = None
    language: Optional[str] = None
    is_generated: Optional[bool] = None
    transcript_text: str = ""
    segments: list[TranscriptSegment] = field(default_factory=list)
    no_transcript: bool = False
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segments"] = [asdict(segment) for segment in self.segments]
        return payload
