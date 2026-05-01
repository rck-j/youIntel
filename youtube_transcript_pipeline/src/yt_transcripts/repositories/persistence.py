from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from yt_transcripts.db.models import AnalysisRun, Channel, ChannelMetricSnapshot, Transcript, Video, VideoAnalysis, VideoMetricSnapshot


def upsert_channel(session: Session, *, youtube_channel_id: str, title: str, url: str, subscriber_count: int | None = None, total_view_count: int | None = None, video_count: int | None = None) -> Channel:
    channel = get_channel_by_youtube_id(session, youtube_channel_id=youtube_channel_id)
    if channel:
        channel.title = title
        channel.url = url
        channel.subscriber_count = subscriber_count
        channel.total_view_count = total_view_count
        channel.video_count = video_count
        return channel
    channel = Channel(youtube_channel_id=youtube_channel_id, title=title, url=url, subscriber_count=subscriber_count, total_view_count=total_view_count, video_count=video_count)
    session.add(channel)
    session.flush()
    return channel


def create_channel_metric_snapshot(session: Session, *, channel_id: int, subscriber_count: int | None, total_view_count: int | None, video_count: int | None) -> ChannelMetricSnapshot:
    row = ChannelMetricSnapshot(channel_id=channel_id, subscriber_count=subscriber_count, total_view_count=total_view_count, video_count=video_count)
    session.add(row)
    return row


def get_channel_by_youtube_id(session: Session, *, youtube_channel_id: str) -> Channel | None:
    return session.scalar(select(Channel).where(Channel.youtube_channel_id == youtube_channel_id))


def list_channels(session: Session) -> list[Channel]: return list(session.scalars(select(Channel).order_by(Channel.title.asc())).all())


def upsert_video(session: Session, *, channel_id: int, youtube_video_id: str, title: str, url: str, published_at: datetime | None, duration_seconds: int | None, is_short: bool, view_count: int | None = None, like_count: int | None = None, comment_count: int | None = None) -> Video:
    video = get_video_by_youtube_id(session, youtube_video_id=youtube_video_id)
    if video:
        video.channel_id = channel_id; video.title = title; video.url = url; video.published_at = published_at; video.duration_seconds = duration_seconds; video.is_short = is_short
        video.view_count = view_count; video.like_count = like_count; video.comment_count = comment_count
        return video
    video = Video(channel_id=channel_id, youtube_video_id=youtube_video_id, title=title, url=url, published_at=published_at, duration_seconds=duration_seconds, is_short=is_short, view_count=view_count, like_count=like_count, comment_count=comment_count)
    session.add(video); session.flush(); return video


def create_video_metric_snapshot(session: Session, *, video_id: int, published_at: datetime | None, view_count: int | None, like_count: int | None, comment_count: int | None) -> VideoMetricSnapshot:
    hours_since_publish = None
    if published_at:
        hours_since_publish = int((datetime.now(timezone.utc) - published_at.astimezone(timezone.utc)).total_seconds() // 3600)
    row = VideoMetricSnapshot(video_id=video_id, hours_since_publish=hours_since_publish, view_count=view_count, like_count=like_count, comment_count=comment_count)
    session.add(row)
    return row


def get_video_metric_snapshot_at_hours(session: Session, *, video_id: int, target_hours: int, tolerance_hours: int = 2) -> VideoMetricSnapshot | None:
    stmt = select(VideoMetricSnapshot).where(VideoMetricSnapshot.video_id == video_id, VideoMetricSnapshot.hours_since_publish >= target_hours - tolerance_hours, VideoMetricSnapshot.hours_since_publish <= target_hours + tolerance_hours).order_by(VideoMetricSnapshot.captured_at.asc())
    return session.scalar(stmt)


def get_video_by_youtube_id(session: Session, *, youtube_video_id: str) -> Video | None: return session.scalar(select(Video).where(Video.youtube_video_id == youtube_video_id))

def list_latest_videos(session: Session, *, limit: int = 50) -> list[Video]: return list(session.scalars(select(Video).order_by(Video.published_at.desc()).limit(limit)).all())
def list_unprocessed_videos(session: Session) -> list[Video]: return list(session.scalars(select(Video).where(~Video.id.in_(select(AnalysisRun.video_id))).order_by(Video.published_at.desc())).all())

def upsert_transcript(session: Session, *, video_id: int, source: str, language: str | None, raw_transcript_json: dict, normalized_text: str, segment_count: int) -> Transcript:
    transcript = get_transcript_for_video(session, video_id=video_id, source=source, language=language)
    if transcript:
        transcript.raw_transcript_json = raw_transcript_json; transcript.normalized_text = normalized_text; transcript.segment_count = segment_count; transcript.fetched_at = datetime.utcnow(); return transcript
    transcript = Transcript(video_id=video_id, source=source, language=language, raw_transcript_json=raw_transcript_json, normalized_text=normalized_text, segment_count=segment_count)
    session.add(transcript); session.flush(); return transcript

def get_transcript_for_video(session: Session, *, video_id: int, source: str, language: str | None) -> Transcript | None: return session.scalar(select(Transcript).where(Transcript.video_id == video_id, Transcript.source == source, Transcript.language == language))
def list_videos_missing_transcripts(session: Session) -> list[Video]: return list(session.scalars(select(Video).where(~Video.id.in_(select(Transcript.video_id)))).all())
def get_existing_analysis_run(session: Session, *, video_id: int, analysis_type: str, model_name: str, prompt_version: str) -> AnalysisRun | None: return session.scalar(select(AnalysisRun).where(AnalysisRun.video_id == video_id, AnalysisRun.analysis_type == analysis_type, AnalysisRun.model_name == model_name, AnalysisRun.prompt_version == prompt_version))
def create_analysis_run(session: Session, *, video_id: int, transcript_id: int, analysis_type: str, model_name: str, prompt_version: str, prompt_text: str) -> AnalysisRun: run = AnalysisRun(video_id=video_id, transcript_id=transcript_id, analysis_type=analysis_type, model_name=model_name, prompt_version=prompt_version, prompt_text=prompt_text, status="running"); session.add(run); session.flush(); return run
def complete_analysis_run(session: Session, *, analysis_run: AnalysisRun, raw_response: str, parsed_response_json: dict) -> AnalysisRun: analysis_run.raw_response=raw_response; analysis_run.parsed_response_json=parsed_response_json; analysis_run.status="completed"; analysis_run.error_message=None; return analysis_run
def fail_analysis_run(session: Session, *, analysis_run: AnalysisRun, error_message: str) -> AnalysisRun: analysis_run.status="failed"; analysis_run.error_message=error_message; return analysis_run
def save_video_analysis(session: Session, *, analysis_run_id: int, video_id: int, summary: str | None, main_topics_json: dict | list | None, claims_json: dict | list | None, perspective_json: dict | list | None, sentiment_json: dict | list | None, bias_signals_json: dict | list | None, rhetoric_signals_json: dict | list | None, influence_signals_json: dict | list | None, confidence_score: float | None) -> VideoAnalysis:
    existing = session.scalar(select(VideoAnalysis).where(VideoAnalysis.analysis_run_id == analysis_run_id))
    if existing:
        existing.summary=summary; existing.main_topics_json=main_topics_json; existing.claims_json=claims_json; existing.perspective_json=perspective_json; existing.sentiment_json=sentiment_json; existing.bias_signals_json=bias_signals_json; existing.rhetoric_signals_json=rhetoric_signals_json; existing.influence_signals_json=influence_signals_json; existing.confidence_score=confidence_score; return existing
    row=VideoAnalysis(analysis_run_id=analysis_run_id, video_id=video_id, summary=summary, main_topics_json=main_topics_json, claims_json=claims_json, perspective_json=perspective_json, sentiment_json=sentiment_json, bias_signals_json=bias_signals_json, rhetoric_signals_json=rhetoric_signals_json, influence_signals_json=influence_signals_json, confidence_score=confidence_score); session.add(row); session.flush(); return row

def list_videos_missing_analysis(session: Session) -> list[Video]: return list(session.scalars(select(Video).where(~Video.id.in_(select(VideoAnalysis.video_id)))).all())
