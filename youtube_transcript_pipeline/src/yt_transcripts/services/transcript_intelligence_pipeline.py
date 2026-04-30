from __future__ import annotations

import json
from errno import EACCES, EROFS
from pathlib import Path

from yt_transcripts.db.session import SessionLocal
from sqlalchemy import select

from yt_transcripts.db.models import Transcript
from yt_transcripts.repositories.persistence import (
    complete_analysis_run,
    create_analysis_run,
    get_existing_analysis_run,
    get_video_by_youtube_id,
    save_video_analysis,
)
from yt_transcripts.services.prompt_service import PromptService
from yt_transcripts.services.topic_aggregation_service import TopicAggregationService
from yt_transcripts.services.topic_perspective_analysis_service import TopicPerspectiveAnalysisService


class TranscriptIntelligencePipeline:
    def __init__(self, prompt_service: PromptService | None = None, analysis_service: TopicPerspectiveAnalysisService | None = None, aggregation_service: TopicAggregationService | None = None) -> None:
        self.prompt_service = prompt_service or PromptService()
        self.analysis_service = analysis_service or TopicPerspectiveAnalysisService()
        self.aggregation_service = aggregation_service or TopicAggregationService()

    def run(self, *, input_dir: str, model: str, prompt_file: str, output_file: str | None = None, prompt_version: str = "v1", force: bool = False) -> dict:
        prompt_text = self.prompt_service.load_prompt(prompt_file)
        transcript_records = self._load_transcript_records(input_dir)

        analysis_rows: list[dict] = []
        with SessionLocal() as session:
            for record in transcript_records:
                transcript_text = record.get("transcript_text", "")
                if not transcript_text:
                    continue
                db_video = get_video_by_youtube_id(session, youtube_video_id=record.get("video_id", ""))
                if not db_video:
                    continue
                existing = get_existing_analysis_run(session, video_id=db_video.id, analysis_type="topic_perspective", model_name=model, prompt_version=prompt_version)
                if existing and existing.status == "completed" and not force:
                    continue
                transcript_row = session.scalar(select(Transcript).where(Transcript.video_id == db_video.id))
                if not transcript_row:
                    continue
                run = existing or create_analysis_run(session, video_id=db_video.id, transcript_id=transcript_row.id, analysis_type="topic_perspective", model_name=model, prompt_version=prompt_version, prompt_text=prompt_text)

                analysis_payload = self.analysis_service.analyze(model=model, prompt_text=prompt_text, transcript_text=transcript_text, video_id=record.get("video_id", ""), channel_id=record.get("channel_id"), channel_title=record.get("channel_title"))
                raw_response = json.dumps(analysis_payload)
                complete_analysis_run(session, analysis_run=run, raw_response=raw_response, parsed_response_json=analysis_payload)
                save_video_analysis(
                    session,
                    analysis_run_id=run.id,
                    video_id=db_video.id,
                    summary=analysis_payload.get("summary"),
                    main_topics_json=analysis_payload.get("main_topics") or analysis_payload.get("topics"),
                    claims_json=analysis_payload.get("claims"),
                    perspective_json=analysis_payload.get("perspective"),
                    sentiment_json=analysis_payload.get("sentiment"),
                    bias_signals_json=analysis_payload.get("bias_signals"),
                    rhetoric_signals_json=analysis_payload.get("rhetoric_signals"),
                    influence_signals_json=analysis_payload.get("influence_signals"),
                    confidence_score=analysis_payload.get("confidence_score"),
                )
                session.commit()
                analysis_rows.append({"video_id": record.get("video_id"), "channel_id": record.get("channel_id"), "channel_title": record.get("channel_title"), "analysis": analysis_payload})

        aggregated_collections = self.aggregation_service.aggregate(analysis_rows)
        result = {"model": model, "input_dir": str(Path(input_dir).resolve()), "analyzed_videos": len(analysis_rows), "aggregations": aggregated_collections}

        if output_file:
            output_path = Path(output_file)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            except OSError as exc:
                if exc.errno in {EACCES, EROFS}:
                    raise RuntimeError("Output path is not writable. " f"Received --output-file '{output_file}'. " "Use a writable project path such as " "'outputs/topic_perspectives_aggregate.json'.") from exc
                raise

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
            records.append({"video_id": video.get("video_id"), "channel_id": video.get("channel_id"), "channel_title": video.get("channel_title"), "transcript_text": transcript.get("transcript_text", "")})
        return records
