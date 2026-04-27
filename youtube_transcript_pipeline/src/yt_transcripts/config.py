from __future__ import annotations

import logging
import os

from dotenv import load_dotenv


load_dotenv()


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_transcript_duration_bounds() -> tuple[int, int]:
    min_seconds = int(os.getenv("TRANSCRIPT_MIN_VIDEO_SECONDS", "180"))
    max_seconds = int(os.getenv("TRANSCRIPT_MAX_VIDEO_SECONDS", "1200"))
    if min_seconds < 0:
        raise ValueError("TRANSCRIPT_MIN_VIDEO_SECONDS must be >= 0.")
    if max_seconds < min_seconds:
        raise ValueError("TRANSCRIPT_MAX_VIDEO_SECONDS must be >= TRANSCRIPT_MIN_VIDEO_SECONDS.")
    return min_seconds, max_seconds
