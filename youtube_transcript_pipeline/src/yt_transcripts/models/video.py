from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class VideoItem:
    video_id: str
    title: str
    url: str
    duration_seconds: Optional[int] = None
    published_at: Optional[str] = None
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    description: Optional[str] = None
