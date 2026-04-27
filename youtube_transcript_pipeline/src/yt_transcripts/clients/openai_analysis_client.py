from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


class OpenAIAnalysisClient:
    """Client wrapper for transcript analysis with OpenAI models."""

    def __init__(self, api_key: str | None = None) -> None:
        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def analyze_topics_and_perspectives(
        self,
        *,
        model: str,
        system_prompt: str,
        transcript_text: str,
        video_id: str,
        channel_id: str | None,
        channel_title: str | None,
    ) -> dict[str, Any]:
        user_prompt = (
            "Analyze this transcript and return JSON matching the requested schema.\n"
            f"video_id: {video_id}\n"
            f"channel_id: {channel_id or ''}\n"
            f"channel_title: {channel_title or ''}\n\n"
            f"transcript:\n{transcript_text}"
        )

        response = self._client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
        )

        response_text = response.output_text.strip()
        return self._parse_json(response_text)

    @staticmethod
    def _parse_json(response_text: str) -> dict[str, Any]:
        try:
            payload = json.loads(response_text)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

        start = response_text.find("{")
        end = response_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = response_text[start : end + 1]
            try:
                payload = json.loads(candidate)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                pass

        return {"topics": []}
