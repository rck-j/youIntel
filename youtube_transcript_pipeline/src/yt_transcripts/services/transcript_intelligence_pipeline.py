from __future__ import annotations

import json
from pathlib import Path

from yt_transcripts.services.prompt_service import PromptService
from yt_transcripts.services.topic_aggregation_service import TopicAggregationService
from yt_transcripts.services.topic_perspective_analysis_service import TopicPerspectiveAnalysisService


class TranscriptIntelligencePipeline:
    """Orchestrates transcript-topic analysis and cross-channel aggregation."""

    def __init__(
        self,
        prompt_service: PromptService | None = None,
        analysis_service: TopicPerspectiveAnalysisService | None = None,
        aggregation_service: TopicAggregationService | None = None,
    ) -> None:
        self.prompt_service = prompt_service or PromptService()
        self.analysis_service = analysis_service or TopicPerspectiveAnalysisService()
        self.aggregation_service = aggregation_service or TopicAggregationService()

    def run(
        self,
        *,
        input_dir: str,
        model: str,
        prompt_file: str,
        output_file: str | None = None,
    ) -> dict:
        prompt_text = self.prompt_service.load_prompt(prompt_file)
        transcript_records = self._load_transcript_records(input_dir)

        analysis_rows: list[dict] = []
        for record in transcript_records:
            transcript_text = record.get("transcript_text", "")
            if not transcript_text:
                continue

            topics = self.analysis_service.analyze(
                model=model,
                prompt_text=prompt_text,
                transcript_text=transcript_text,
                video_id=record.get("video_id", ""),
                channel_id=record.get("channel_id"),
                channel_title=record.get("channel_title"),
            )
            analysis_rows.append(
                {
                    "video_id": record.get("video_id"),
                    "channel_id": record.get("channel_id"),
                    "channel_title": record.get("channel_title"),
                    "topics": topics,
                }
            )

        aggregated_topics = self.aggregation_service.aggregate(analysis_rows)
        result = {
            "model": model,
            "input_dir": str(Path(input_dir).resolve()),
            "analyzed_videos": len(analysis_rows),
            "topics": aggregated_topics,
        }

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        return result

    @staticmethod
    def _load_transcript_records(input_dir: str) -> list[dict]:
        records: list[dict] = []
        for file_path in sorted(Path(input_dir).glob("*.json")):
            if file_path.name in {"batch_summary.json", "topic_perspectives_aggregate.json"}:
                continue

            payload = json.loads(file_path.read_text(encoding="utf-8"))
            transcript = payload.get("transcript", {})
            video = payload.get("video", {})
            if transcript.get("no_transcript"):
                continue

            records.append(
                {
                    "video_id": video.get("video_id"),
                    "channel_id": video.get("channel_id"),
                    "channel_title": video.get("channel_title"),
                    "transcript_text": transcript.get("transcript_text", ""),
                }
            )
        return records
