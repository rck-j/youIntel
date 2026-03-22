from __future__ import annotations

import os
from typing import Optional

from googleapiclient.discovery import build

from yt_transcripts.models.video import VideoItem


class YouTubeDataClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required.")
        self._service = build("youtube", "v3", developerKey=self.api_key)

    def get_uploads_playlist_id(self, channel_id: str) -> str:
        response = (
            self._service.channels()
            .list(part="contentDetails", id=channel_id)
            .execute()
        )
        items = response.get("items", [])
        if not items:
            raise ValueError(f"Channel not found: {channel_id}")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def get_latest_videos(self, channel_id: str, max_results: int = 5) -> list[VideoItem]:
        uploads_playlist_id = self.get_uploads_playlist_id(channel_id)
        response = (
            self._service.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=max_results,
            )
            .execute()
        )

        videos: list[VideoItem] = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            resource_id = snippet.get("resourceId", {})
            video_id = resource_id.get("videoId")
            if not video_id:
                continue
            videos.append(
                VideoItem(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    published_at=snippet.get("publishedAt"),
                    channel_id=snippet.get("channelId"),
                    channel_title=snippet.get("channelTitle"),
                    description=snippet.get("description"),
                )
            )
        return videos
