from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect, text


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///yt_transcripts.db")


def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    columns = inspector.get_columns(table_name)
    return any(column.get("name") == column_name for column in columns)


def _add_column_if_missing(connection, inspector, table_name: str, column_name: str, sql_type: str) -> bool:
    if _column_exists(inspector, table_name, column_name):
        return False
    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"))
    return True


def main() -> None:
    engine = create_engine(_database_url(), future=True)

    applied: list[str] = []
    with engine.begin() as connection:
        inspector = inspect(connection)

        if "channels" not in inspector.get_table_names() or "videos" not in inspector.get_table_names():
            raise RuntimeError("Expected tables 'channels' and 'videos' to exist. Run init-db before this migration.")

        if _add_column_if_missing(connection, inspector, "channels", "subscriber_count", "INTEGER"):
            applied.append("channels.subscriber_count")

        inspector = inspect(connection)
        if _add_column_if_missing(connection, inspector, "videos", "view_count", "INTEGER"):
            applied.append("videos.view_count")

        inspector = inspect(connection)
        if _add_column_if_missing(connection, inspector, "videos", "like_count", "INTEGER"):
            applied.append("videos.like_count")

    if applied:
        print("Migration complete. Added columns:")
        for item in applied:
            print(f"- {item}")
    else:
        print("Migration complete. No changes were required.")


if __name__ == "__main__":
    main()
