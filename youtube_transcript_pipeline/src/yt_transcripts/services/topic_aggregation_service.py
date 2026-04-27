from __future__ import annotations

from collections import defaultdict


class TopicAggregationService:
    """Aggregates topics across channels and preserves channel perspectives."""

    def aggregate(self, analysis_rows: list[dict]) -> list[dict]:
        topic_buckets: dict[str, dict] = {}

        for row in analysis_rows:
            for topic_item in row.get("topics", []):
                topic_name = topic_item["topic"].strip()
                topic_key = topic_name.casefold()
                perspective = topic_item["perspective"].strip()

                bucket = topic_buckets.setdefault(
                    topic_key,
                    {
                        "topic": topic_name,
                        "channels": defaultdict(lambda: {"channel_id": None, "channel_title": None, "perspectives": set(), "videos": set()}),
                    },
                )

                channel_key = row.get("channel_id") or row.get("channel_title") or "unknown_channel"
                channel_entry = bucket["channels"][channel_key]
                channel_entry["channel_id"] = row.get("channel_id")
                channel_entry["channel_title"] = row.get("channel_title")
                channel_entry["perspectives"].add(perspective)
                channel_entry["videos"].add(row.get("video_id"))

        aggregated_topics: list[dict] = []
        for bucket in topic_buckets.values():
            channels = []
            for channel_data in bucket["channels"].values():
                channels.append(
                    {
                        "channel_id": channel_data["channel_id"],
                        "channel_title": channel_data["channel_title"],
                        "perspectives": sorted(channel_data["perspectives"]),
                        "video_ids": sorted(video_id for video_id in channel_data["videos"] if video_id),
                    }
                )

            aggregated_topics.append(
                {
                    "topic": bucket["topic"],
                    "channels": sorted(
                        channels,
                        key=lambda item: (
                            item["channel_title"] or "",
                            item["channel_id"] or "",
                        ),
                    ),
                }
            )

        return sorted(aggregated_topics, key=lambda item: item["topic"].casefold())
