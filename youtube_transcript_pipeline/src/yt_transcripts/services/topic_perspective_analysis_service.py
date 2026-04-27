from __future__ import annotations

from typing import Any

from yt_transcripts.clients.openai_analysis_client import OpenAIAnalysisClient


class TopicPerspectiveAnalysisService:
    """Runs topic/perspective extraction for a single transcript."""

    def __init__(self, openai_client: OpenAIAnalysisClient | None = None) -> None:
        self.openai_client = openai_client or OpenAIAnalysisClient()

    def analyze(
        self,
        *,
        model: str,
        prompt_text: str,
        transcript_text: str,
        video_id: str,
        channel_id: str | None,
        channel_title: str | None,
    ) -> list[dict[str, str]]:
        payload = self.openai_client.analyze_topics_and_perspectives(
            model=model,
            system_prompt=prompt_text,
            transcript_text=transcript_text,
            video_id=video_id,
            channel_id=channel_id,
            channel_title=channel_title,
        )
        topics = payload.get("topics", [])
        if not isinstance(topics, list):
            return []

        cleaned_topics: list[dict[str, str]] = []
        for entry in topics:
            if not isinstance(entry, dict):
                continue
            topic = str(entry.get("topic", "")).strip()
            perspective = str(entry.get("perspective", "")).strip()
            if not topic or not perspective:
                continue
            cleaned_topics.append({"topic": topic, "perspective": perspective})
        return cleaned_topics
