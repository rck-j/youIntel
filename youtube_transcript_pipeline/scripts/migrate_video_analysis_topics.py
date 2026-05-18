from __future__ import annotations

import json

from sqlalchemy import inspect, text

from yt_transcripts.db.session import _normalized_database_url, get_engine


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def main() -> None:
    db_url = _normalized_database_url()
    engine = get_engine(database_url=db_url)

    with engine.begin() as connection:
        inspector = inspect(connection)

        if not _table_exists(inspector, "video_analysis"):
            connection.execute(
                text(
                    """
                    CREATE TABLE video_analysis (
                        id INTEGER PRIMARY KEY,
                        analysis_run_id INTEGER NOT NULL,
                        video_id INTEGER NOT NULL,
                        topic VARCHAR(512),
                        summary TEXT,
                        perspective TEXT,
                        framing TEXT,
                        narrative TEXT,
                        rhetoric_json JSON,
                        influence TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        FOREIGN KEY(analysis_run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
                        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
                    )
                    """
                )
            )

        inspector = inspect(connection)
        if not _index_exists(inspector, "video_analysis", "ix_video_analysis_analysis_run_id"):
            connection.execute(text("CREATE INDEX ix_video_analysis_analysis_run_id ON video_analysis (analysis_run_id)"))
        if not _index_exists(inspector, "video_analysis", "ix_video_analysis_video_id"):
            connection.execute(text("CREATE INDEX ix_video_analysis_video_id ON video_analysis (video_id)"))
        if not _index_exists(inspector, "video_analysis", "ix_video_analysis_topic"):
            connection.execute(text("CREATE INDEX ix_video_analysis_topic ON video_analysis (topic)"))

        if _table_exists(inspector, "video_analyses"):
            legacy_rows = connection.execute(
                text("SELECT analysis_run_id, video_id, main_topics_json FROM video_analyses WHERE main_topics_json IS NOT NULL")
            ).mappings()
            for row in legacy_rows:
                connection.execute(
                    text("DELETE FROM video_analysis WHERE analysis_run_id = :analysis_run_id AND video_id = :video_id"),
                    {"analysis_run_id": row["analysis_run_id"], "video_id": row["video_id"]},
                )
                topics = row["main_topics_json"]
                if isinstance(topics, str):
                    try:
                        topics = json.loads(topics)
                    except json.JSONDecodeError:
                        topics = []
                if not isinstance(topics, list):
                    continue

                for topic_payload in topics:
                    if not isinstance(topic_payload, dict):
                        continue
                    analysis = topic_payload.get("analysis") if isinstance(topic_payload.get("analysis"), dict) else {}
                    rhetoric = analysis.get("rhetoric")
                    connection.execute(
                        text(
                            """
                            INSERT INTO video_analysis (
                                analysis_run_id, video_id, topic, summary, perspective,
                                framing, narrative, rhetoric_json, influence
                            ) VALUES (
                                :analysis_run_id, :video_id, :topic, :summary, :perspective,
                                :framing, :narrative, :rhetoric_json, :influence
                            )
                            """
                        ),
                        {
                            "analysis_run_id": row["analysis_run_id"],
                            "video_id": row["video_id"],
                            "topic": topic_payload.get("topic"),
                            "summary": topic_payload.get("summary"),
                            "perspective": topic_payload.get("perspective"),
                            "framing": analysis.get("framing"),
                            "narrative": analysis.get("narrative"),
                            "rhetoric_json": json.dumps(rhetoric) if rhetoric is not None else None,
                            "influence": analysis.get("influence"),
                        },
                    )

    print("Migration complete: video_analysis table and indexes are ready; backfill attempted from video_analyses.")


if __name__ == "__main__":
    main()
