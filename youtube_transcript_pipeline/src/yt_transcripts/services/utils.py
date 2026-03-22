from __future__ import annotations

import re

YOUTUBE_URL_PATTERNS = [
    r"(?:v=)([0-9A-Za-z_-]{11})",
    r"(?:youtu\.be/)([0-9A-Za-z_-]{11})",
    r"(?:shorts/)([0-9A-Za-z_-]{11})",
    r"(?:embed/)([0-9A-Za-z_-]{11})",
]


def extract_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", value):
        return value
    for pattern in YOUTUBE_URL_PATTERNS:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract a YouTube video ID from: {value}")
