from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Optional

import yt_dlp

from yt_transcripts.models.transcript import TranscriptResult, TranscriptSegment


class YtDlpSubtitleClient:
    def fetch(self, video_url: str, video_id: str, languages: list[str]) -> TranscriptResult:
        subtitle_langs = languages or ["en", "en-US", "en-GB"]

        with tempfile.TemporaryDirectory(prefix="yt_subs_") as tmp_dir:
            output_template = str(Path(tmp_dir) / "%(id)s.%(ext)s")
            ydl_opts: dict[str, Any] = {
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": subtitle_langs,
                "subtitlesformat": "json3/vtt/best",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

            subtitle_files = list(Path(tmp_dir).glob(f"{video_id}*"))
            parsed = self._parse_downloaded_subtitle_files(subtitle_files)
            if parsed is None:
                raise RuntimeError("yt-dlp did not produce a readable subtitle file")

            segments, metadata = parsed
            return TranscriptResult(
                video_id=video_id,
                source="yt_dlp",
                language_code=metadata.get("language_code"),
                language=metadata.get("language"),
                is_generated=metadata.get("is_generated"),
                transcript_text=" ".join(segment.text for segment in segments).strip(),
                segments=segments,
                metadata={
                    "phase": "yt_dlp",
                    "requested_languages": subtitle_langs,
                    "title": info.get("title"),
                    **metadata,
                },
            )

    def _parse_downloaded_subtitle_files(
        self, subtitle_files: list[Path]
    ) -> Optional[tuple[list[TranscriptSegment], dict[str, Any]]]:
        json3_files = [p for p in subtitle_files if p.suffix == ".json3"]
        vtt_files = [p for p in subtitle_files if p.suffix == ".vtt"]

        for path in json3_files:
            parsed = self._parse_json3_subtitle(path)
            if parsed:
                return parsed

        for path in vtt_files:
            parsed = self._parse_vtt_subtitle(path)
            if parsed:
                return parsed
        return None

    def _parse_json3_subtitle(
        self, path: Path
    ) -> Optional[tuple[list[TranscriptSegment], dict[str, Any]]]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        events = payload.get("events", [])
        segments: list[TranscriptSegment] = []

        for event in events:
            start_ms = event.get("tStartMs")
            duration_ms = event.get("dDurationMs", 0)
            segs = event.get("segs", [])
            text = " ".join(
                seg.get("utf8", "").replace("\n", " ").strip() for seg in segs if seg.get("utf8")
            ).strip()
            if not text or start_ms is None:
                continue
            segments.append(
                TranscriptSegment(
                    text=text,
                    start=float(start_ms) / 1000.0,
                    duration=float(duration_ms) / 1000.0,
                )
            )

        if not segments:
            return None

        filename = path.name.lower()
        metadata = {
            "language_code": self._infer_language_code_from_filename(filename),
            "language": None,
            "is_generated": "auto" in filename,
            "subtitle_file": str(path),
            "subtitle_format": "json3",
        }
        return segments, metadata

    def _parse_vtt_subtitle(
        self, path: Path
    ) -> Optional[tuple[list[TranscriptSegment], dict[str, Any]]]:
        lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
        segments: list[TranscriptSegment] = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if "-->" not in line:
                i += 1
                continue

            start_str, end_str = [part.strip() for part in line.split("-->", 1)]
            i += 1
            text_lines: list[str] = []
            while i < len(lines) and lines[i].strip():
                current = re.sub(r"<[^>]+>", "", lines[i]).strip()
                if current:
                    text_lines.append(current)
                i += 1

            text = " ".join(text_lines).strip()
            if text:
                start = self._parse_vtt_timestamp(start_str)
                end = self._parse_vtt_timestamp(end_str.split(" ")[0])
                segments.append(
                    TranscriptSegment(text=text, start=start, duration=max(0.0, end - start))
                )
            i += 1

        if not segments:
            return None

        filename = path.name.lower()
        metadata = {
            "language_code": self._infer_language_code_from_filename(filename),
            "language": None,
            "is_generated": "auto" in filename,
            "subtitle_file": str(path),
            "subtitle_format": "vtt",
        }
        return segments, metadata

    @staticmethod
    def _parse_vtt_timestamp(value: str) -> float:
        parts = value.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        raise ValueError(f"Unsupported VTT timestamp: {value}")

    @staticmethod
    def _infer_language_code_from_filename(filename: str) -> Optional[str]:
        match = re.search(r"\.([a-z]{2,3}(?:-[a-z]{2,3})?)\.", filename)
        return match.group(1) if match else None
